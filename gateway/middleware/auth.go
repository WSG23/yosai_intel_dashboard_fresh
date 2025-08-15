package middleware

import (
	"context"
	"crypto/rsa"
	"crypto/x509"
	"encoding/json"
	"encoding/pem"
	"errors"
	"io"
	"net/http"
	"strings"
	"sync"
	"time"

	"github.com/bits-and-blooms/bloom/v3"
	"github.com/golang-jwt/jwt/v5"
	"github.com/prometheus/client_golang/prometheus"
	"github.com/redis/go-redis/v9"
	"github.com/sony/gobreaker"

	xerrors "github.com/WSG23/errors"

	"github.com/WSG23/yosai-gateway/internal/auth"
	"github.com/WSG23/yosai-gateway/internal/tracing"
)

// JWTConfig holds configuration for JWT validation and refresh.
type JWTConfig struct {
	PublicKeys    []string      // PEM encoded RSA public keys
	RefreshURL    string        // optional token refresh endpoint
	RefreshBefore time.Duration // duration before expiry to trigger refresh
	MaxJSONBytes  int64         // max bytes to read from JSON responses; 0 for unlimited
	Client        *http.Client  // HTTP client used for refresh requests
	Audience      string        // expected audience for tokens (optional)
}

// TokenCache caches validated tokens and tracks blacklisted JTIs.
type TokenCache struct {
	redis    *redis.Client
	blFilter *bloom.BloomFilter
	mu       sync.RWMutex
}

// NewTokenCache creates a TokenCache using the given redis client.
func NewTokenCache(rdb *redis.Client) *TokenCache {
	// Estimate capacity for blacklisted JTIs. False positive rate 1%.
	// The bloom filter prevents unnecessary Redis lookups for tokens that
	// have never been blacklisted.
	filter := bloom.NewWithEstimates(100000, 0.01)
	return &TokenCache{redis: rdb, blFilter: filter}
}

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
	tc.mu.RLock()
	inFilter := tc.blFilter.TestString(jti)
	tc.mu.RUnlock()
	if !inFilter {
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
	tc.mu.Lock()
	tc.blFilter.AddString(jti)
	tc.mu.Unlock()
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
	if cfg.Client == nil {
		cfg.Client = http.DefaultClient
	}
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

func (am *AuthMiddleware) parser() *jwt.Parser {
	opts := []jwt.ParserOption{jwt.WithValidMethods([]string{jwt.SigningMethodRS256.Alg()})}
	if am.cfg.Audience != "" {
		opts = append(opts, jwt.WithAudience(am.cfg.Audience))
	}
	return jwt.NewParser(opts...)
}

func reasonFromError(err error) string {
	switch {
	case errors.Is(err, jwt.ErrTokenExpired):
		return "expired"
	case errors.Is(err, jwt.ErrTokenInvalidAudience):
		return "invalid_aud"
	case errors.Is(err, jwt.ErrTokenSignatureInvalid):
		return "invalid_signature"
	case errors.Is(err, jwt.ErrTokenNotValidYet):
		return "not_yet_valid"
	case errors.Is(err, jwt.ErrTokenInvalidIssuer):
		return "invalid_iss"
	case errors.Is(err, jwt.ErrTokenMalformed):
		return "malformed"
	default:
		return "invalid"
	}
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
		resp, err := am.cfg.Client.Do(req)
		if err != nil {
			return nil, err
		}
		defer resp.Body.Close()
		if resp.StatusCode != http.StatusOK {
			return nil, xerrors.Errorf("refresh failed: %s", resp.Status)
		}
		var reader io.Reader = resp.Body
		if am.cfg.MaxJSONBytes > 0 {
			reader = io.LimitReader(resp.Body, am.cfg.MaxJSONBytes)
		}
		body, err := io.ReadAll(reader)
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
	parser := am.parser()
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
			tracing.Logger.WithField("reason", "missing").Warn("authorization failed")
                    xerrors.WriteJSON(w, http.StatusUnauthorized, xerrors.Unauthorized, "unauthorized", map[string]string{"reason": "missing"})
			return
		}
		parts := strings.Fields(authHdr)
		if len(parts) != 2 || !strings.EqualFold(parts[0], "Bearer") {
			authFailures.Inc()
			tracing.Logger.WithField("reason", "invalid_header").Warn("authorization failed")
                    xerrors.WriteJSON(w, http.StatusUnauthorized, xerrors.Unauthorized, "unauthorized", map[string]string{"reason": "invalid_header"})
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
		parser := am.parser()
		token, err := parser.ParseWithClaims(tokenStr, claims, am.keyFunc)
		if err != nil || !token.Valid {
			reason := reasonFromError(err)
			tracing.Logger.WithError(err).WithField("reason", reason).Warn("invalid token")
			authFailures.Inc()
                    xerrors.WriteJSON(w, http.StatusUnauthorized, xerrors.Unauthorized, "unauthorized", map[string]string{"reason": reason})
			return
		}
		if am.cache != nil {
			black, err := am.cache.IsBlacklisted(ctx, claims.ID)
			if err == nil && black {
				authFailures.Inc()
				tracing.Logger.WithField("reason", "blacklisted").Warn("token blacklisted")
                            xerrors.WriteJSON(w, http.StatusForbidden, xerrors.Unauthorized, "forbidden", map[string]string{"reason": "blacklisted"})
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
