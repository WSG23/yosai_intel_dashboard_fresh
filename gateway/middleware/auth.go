package middleware

import (
	"context"
	"crypto/rsa"
	"crypto/x509"
	"encoding/json"
	"encoding/pem"
	"errors"
	"fmt"
	"io"
	"net/http"
	"strings"
	"time"

	"github.com/golang-jwt/jwt/v5"
	"github.com/prometheus/client_golang/prometheus"
	"github.com/redis/go-redis/v9"
	"github.com/sony/gobreaker"

	"github.com/WSG23/yosai-gateway/internal/auth"
	"github.com/WSG23/yosai-gateway/internal/tracing"
	sharederrors "github.com/WSG23/yosai_intel_dashboard_fresh/shared/errors"
)

// JWTConfig holds configuration for JWT validation and refresh.
type JWTConfig struct {
	PublicKeys    []string      // PEM encoded RSA public keys
	RefreshURL    string        // optional token refresh endpoint
	RefreshBefore time.Duration // duration before expiry to trigger refresh
}

// TokenCache caches validated tokens and tracks blacklisted JTIs.
type TokenCache struct {
	redis *redis.Client
}

// NewTokenCache creates a TokenCache using the given redis client.
func NewTokenCache(rdb *redis.Client) *TokenCache { return &TokenCache{redis: rdb} }

func (tc *TokenCache) cacheKey(token string) string   { return "jwt:" + token }
func (tc *TokenCache) blacklistKey(jti string) string { return "bl:" + jti }

// CachedClaims returns cached claims for token if present.
func (tc *TokenCache) CachedClaims(ctx context.Context, token string) (*auth.EnhancedClaims, error) {
	val, err := tc.redis.Get(ctx, tc.cacheKey(token)).Result()
	if err != nil {
		if err == redis.Nil {
			return nil, nil
		}
		return nil, err
	}
	var c auth.EnhancedClaims
	if err := json.Unmarshal([]byte(val), &c); err != nil {
		return nil, err
	}
	return &c, nil
}

// StoreClaims caches claims for token with ttl.
func (tc *TokenCache) StoreClaims(ctx context.Context, token string, claims *auth.EnhancedClaims, ttl time.Duration) error {
	data, err := json.Marshal(claims)
	if err != nil {
		return err
	}
	return tc.redis.Set(ctx, tc.cacheKey(token), data, ttl).Err()
}

// IsBlacklisted checks whether jti is blacklisted.
func (tc *TokenCache) IsBlacklisted(ctx context.Context, jti string) (bool, error) {
	if jti == "" {
		return false, nil
	}
	res, err := tc.redis.Exists(ctx, tc.blacklistKey(jti)).Result()
	if err != nil {
		return false, err
	}
	return res > 0, nil
}

// Blacklist marks jti as invalid for ttl duration.
func (tc *TokenCache) Blacklist(ctx context.Context, jti string, ttl time.Duration) error {
	if jti == "" {
		return nil
	}
	return tc.redis.Set(ctx, tc.blacklistKey(jti), 1, ttl).Err()
}

var (
	authFailures = prometheus.NewCounter(prometheus.CounterOpts{
		Name: "auth_failures_total",
		Help: "Number of failed authentication attempts",
	})
)

func init() {
	prometheus.MustRegister(authFailures)
}

// AuthMiddleware implements JWT authentication with caching and rate limiting.
type AuthMiddleware struct {
	cfg     JWTConfig
	keys    []*rsa.PublicKey
	cache   *TokenCache
	limiter *RateLimiter
	breaker *gobreaker.CircuitBreaker
}

// NewAuthMiddleware creates a configured AuthMiddleware.
func NewAuthMiddleware(cfg JWTConfig, cache *TokenCache, rl *RateLimiter, settings gobreaker.Settings) (*AuthMiddleware, error) {
	am := &AuthMiddleware{cfg: cfg, cache: cache, limiter: rl, breaker: gobreaker.NewCircuitBreaker(settings)}
	for _, pemStr := range cfg.PublicKeys {
		block, _ := pem.Decode([]byte(pemStr))
		if block == nil {
			return nil, errors.New("invalid public key")
		}
		pub, err := x509.ParsePKIXPublicKey(block.Bytes)
		if err != nil {
			return nil, err
		}
		rsaKey, ok := pub.(*rsa.PublicKey)
		if !ok {
			return nil, errors.New("not RSA public key")
		}
		am.keys = append(am.keys, rsaKey)
	}
	if len(am.keys) == 0 {
		return nil, errors.New("no public keys provided")
	}
	return am, nil
}

func (am *AuthMiddleware) keyFunc(_ *jwt.Token) (interface{}, error) {
	return am.keys[0], nil
}

// refresh exchanges token using the configured refresh URL.
func (am *AuthMiddleware) refresh(ctx context.Context, token string) (string, *auth.EnhancedClaims, error) {
	if am.cfg.RefreshURL == "" {
		return token, nil, nil
	}
	var newToken string
	_, err := am.breaker.Execute(func() (interface{}, error) {
		req, err := http.NewRequestWithContext(ctx, http.MethodPost, am.cfg.RefreshURL, nil)
		if err != nil {
			return nil, err
		}
		req.Header.Set("Authorization", "Bearer "+token)
		resp, err := http.DefaultClient.Do(req)
		if err != nil {
			return nil, err
		}
		defer resp.Body.Close()
		if resp.StatusCode != http.StatusOK {
			return nil, fmt.Errorf("refresh failed: %s", resp.Status)
		}
		body, err := io.ReadAll(resp.Body)
		if err != nil {
			return nil, err
		}
		newToken = strings.TrimSpace(string(body))
		return nil, nil
	})
	if err != nil {
		return token, nil, err
	}
	claims := &auth.EnhancedClaims{}
	parser := jwt.NewParser(jwt.WithValidMethods([]string{jwt.SigningMethodRS256.Alg()}))
	if _, err := parser.ParseWithClaims(newToken, claims, am.keyFunc); err != nil {
		return token, nil, err
	}
	return newToken, claims, nil
}

// Middleware returns an http.Handler performing authentication.
func (am *AuthMiddleware) Middleware(next http.Handler) http.Handler {
	if am.limiter != nil {
		next = am.limiter.Middleware(next)
	}
	return http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		if r.Method == http.MethodOptions && r.Header.Get("Access-Control-Request-Method") != "" {
			next.ServeHTTP(w, r)
			return
		}
		authHdr := r.Header.Get("Authorization")
		if authHdr == "" {
			authFailures.Inc()
			sharederrors.WriteJSON(w, http.StatusUnauthorized, sharederrors.Unauthorized, "unauthorized", nil)
			return
		}
		parts := strings.Fields(authHdr)
		if len(parts) != 2 || !strings.EqualFold(parts[0], "Bearer") {
			authFailures.Inc()
			sharederrors.WriteJSON(w, http.StatusUnauthorized, sharederrors.Unauthorized, "unauthorized", nil)
			return
		}
		tokenStr := parts[1]
		ctx := r.Context()
		// cached token
		if am.cache != nil {
			if c, err := am.cache.CachedClaims(ctx, tokenStr); err == nil && c != nil {
				if c.ExpiresAt == nil || c.ExpiresAt.After(time.Now()) {
					r.Header.Set("X-User-ID", c.Subject)
					ctx = auth.NewContext(ctx, c)
					next.ServeHTTP(w, r.WithContext(ctx))
					return
				}
			}
		}
		claims := &auth.EnhancedClaims{}
		parser := jwt.NewParser(jwt.WithValidMethods([]string{jwt.SigningMethodRS256.Alg()}))
		token, err := parser.ParseWithClaims(tokenStr, claims, am.keyFunc)
		if err != nil || !token.Valid {
			tracing.Logger.WithError(err).Warn("invalid token")
			authFailures.Inc()
			sharederrors.WriteJSON(w, http.StatusUnauthorized, sharederrors.Unauthorized, "unauthorized", nil)
			return
		}
		if am.cache != nil {
			black, err := am.cache.IsBlacklisted(ctx, claims.ID)
			if err == nil && black {
				authFailures.Inc()
				sharederrors.WriteJSON(w, http.StatusForbidden, sharederrors.Unauthorized, "forbidden", nil)
				return
			}
		}

		if am.cfg.RefreshBefore > 0 && claims.ExpiresAt != nil && time.Until(claims.ExpiresAt.Time) < am.cfg.RefreshBefore {
			if newTok, newClaims, err := am.refresh(ctx, tokenStr); err == nil && newClaims != nil {
				tokenStr = newTok
				claims = newClaims
			} else if err != nil {
				tracing.Logger.WithError(err).Warn("token refresh failed")
			}
		}

		if am.cache != nil {
			ttl := time.Hour
			if claims.ExpiresAt != nil {
				ttl = time.Until(claims.ExpiresAt.Time)
			}
			_ = am.cache.StoreClaims(ctx, tokenStr, claims, ttl)
		}

		r.Header.Set("X-User-ID", claims.Subject)
		ctx = auth.NewContext(ctx, claims)
		next.ServeHTTP(w, r.WithContext(ctx))
	})
}
