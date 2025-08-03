package middleware

import (
	"context"
	"crypto/rand"
	"crypto/rsa"
	"crypto/x509"
	"encoding/pem"
	"net/http"
	"net/http/httptest"
	"testing"
	"time"

	"github.com/alicebob/miniredis/v2"
	"github.com/golang-jwt/jwt/v5"
	"github.com/redis/go-redis/v9"
	"github.com/sony/gobreaker"

	"github.com/WSG23/yosai-gateway/internal/auth"
	gwconfig "github.com/WSG23/yosai-gateway/internal/config"
)

// helper to start miniredis and client
func newRedis(t *testing.T) (*miniredis.Miniredis, *redis.Client) {
	srv, err := miniredis.Run()
	if err != nil {
		t.Fatalf("failed to start redis: %v", err)
	}
	t.Cleanup(srv.Close)
	client := redis.NewClient(&redis.Options{Addr: srv.Addr()})
	return srv, client
}

func genKeys(t *testing.T) (*rsa.PrivateKey, string) {
	priv, err := rsa.GenerateKey(rand.Reader, 2048)
	if err != nil {
		t.Fatalf("gen key: %v", err)
	}
	pubBytes, err := x509.MarshalPKIXPublicKey(&priv.PublicKey)
	if err != nil {
		t.Fatalf("marshal pub: %v", err)
	}
	pubPem := pem.EncodeToMemory(&pem.Block{Type: "PUBLIC KEY", Bytes: pubBytes})
	return priv, string(pubPem)
}

func newMiddleware(t *testing.T, cache *TokenCache, rl *RateLimiter, cfg JWTConfig) *AuthMiddleware {
	am, err := NewAuthMiddleware(cfg, cache, rl, gobreaker.Settings{})
	if err != nil {
		t.Fatalf("new middleware: %v", err)
	}
	return am
}

func newToken(t *testing.T, priv *rsa.PrivateKey, sub, jti string, exp time.Time) string {
	token := jwt.NewWithClaims(jwt.SigningMethodRS256, &auth.EnhancedClaims{
		RegisteredClaims: jwt.RegisteredClaims{
			Subject:   sub,
			ID:        jti,
			Issuer:    "test",
			ExpiresAt: jwt.NewNumericDate(exp),
		},
	})
	s, err := token.SignedString(priv)
	if err != nil {
		t.Fatalf("sign: %v", err)
	}
	return s
}

func TestAuthValidationAndCaching(t *testing.T) {
	srv, client := newRedis(t)
	priv, pub := genKeys(t)
	cache := NewTokenCache(client)
	am := newMiddleware(t, cache, nil, JWTConfig{PublicKeys: []string{pub}})
	var user string
	handler := am.Middleware(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		user = r.Header.Get("X-User-ID")
		w.WriteHeader(http.StatusOK)
	}))

	tok := newToken(t, priv, "alice", "id1", time.Now().Add(time.Minute))
	req := httptest.NewRequest(http.MethodGet, "/", nil)
	req.Header.Set("Authorization", "Bearer "+tok)
	resp := httptest.NewRecorder()
	handler.ServeHTTP(resp, req)
	if resp.Code != http.StatusOK {
		t.Fatalf("expected 200 got %d", resp.Code)
	}
	if user != "alice" {
		t.Fatalf("missing user header")
	}
	if !srv.Exists("jwt:" + tok) {
		t.Fatalf("token not cached")
	}
}

func TestAuthExpiredToken(t *testing.T) {
	_, client := newRedis(t)
	priv, pub := genKeys(t)
	am := newMiddleware(t, NewTokenCache(client), nil, JWTConfig{PublicKeys: []string{pub}})
	handler := am.Middleware(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) { w.WriteHeader(http.StatusOK) }))

	tok := newToken(t, priv, "bob", "id2", time.Now().Add(-time.Minute))
	req := httptest.NewRequest(http.MethodGet, "/", nil)
	req.Header.Set("Authorization", "Bearer "+tok)
	resp := httptest.NewRecorder()
	handler.ServeHTTP(resp, req)
	if resp.Code != http.StatusUnauthorized {
		t.Fatalf("expected 401 got %d", resp.Code)
	}
}

func TestAuthInvalidSignature(t *testing.T) {
	_, client := newRedis(t)
	priv1, pub1 := genKeys(t)
	priv2, _ := genKeys(t)
	am := newMiddleware(t, NewTokenCache(client), nil, JWTConfig{PublicKeys: []string{pub1}})
	handler := am.Middleware(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) { w.WriteHeader(http.StatusOK) }))

	tok := newToken(t, priv2, "bob", "id3", time.Now().Add(time.Minute))
	req := httptest.NewRequest(http.MethodGet, "/", nil)
	req.Header.Set("Authorization", "Bearer "+tok)
	resp := httptest.NewRecorder()
	handler.ServeHTTP(resp, req)
	if resp.Code != http.StatusUnauthorized {
		t.Fatalf("expected 401 got %d", resp.Code)
	}

	// ensure valid token works
	validTok := newToken(t, priv1, "bob", "id3", time.Now().Add(time.Minute))
	req.Header.Set("Authorization", "Bearer "+validTok)
	resp = httptest.NewRecorder()
	handler.ServeHTTP(resp, req)
	if resp.Code != http.StatusOK {
		t.Fatalf("expected 200 got %d", resp.Code)
	}
}

func TestAuthBlacklistedToken(t *testing.T) {
	srv, client := newRedis(t)
	priv, pub := genKeys(t)
	cache := NewTokenCache(client)
	am := newMiddleware(t, cache, nil, JWTConfig{PublicKeys: []string{pub}})
	handler := am.Middleware(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) { w.WriteHeader(http.StatusOK) }))

	tok := newToken(t, priv, "carol", "id4", time.Now().Add(time.Minute))
	cache.Blacklist(context.Background(), "id4", time.Hour)

	req := httptest.NewRequest(http.MethodGet, "/", nil)
	req.Header.Set("Authorization", "Bearer "+tok)
	resp := httptest.NewRecorder()
	handler.ServeHTTP(resp, req)
	if resp.Code != http.StatusForbidden {
		t.Fatalf("expected 403 got %d", resp.Code)
	}
	if srv.Exists("jwt:" + tok) {
		t.Fatalf("token should not be cached when blacklisted")
	}
}

func TestTokenCacheBloomFilter(t *testing.T) {
	srv, client := newRedis(t)
	cache := NewTokenCache(client)
	// Closing Redis should not affect a lookup for an ID that was never
	// blacklisted because the bloom filter allows skipping the Redis call.
	srv.Close()

	ok, err := cache.IsBlacklisted(context.Background(), "unknown")
	if err != nil {
		t.Fatalf("unexpected error: %v", err)
	}
	if ok {
		t.Fatalf("expected not blacklisted")
	}
}

func TestAuthTokenRefresh(t *testing.T) {
	srv, client := newRedis(t)
	priv, pub := genKeys(t)

	var refreshed bool
	var oldTok string
	var newTokStr string
	refreshSrv := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		refreshed = true
		if r.Header.Get("Authorization") != "Bearer "+oldTok {
			t.Fatalf("bad refresh header")
		}
		newTokStr = newToken(t, priv, "dave", "id5", time.Now().Add(time.Minute))
		w.Write([]byte(newTokStr))
	}))
	defer refreshSrv.Close()

	am := newMiddleware(t, NewTokenCache(client), nil, JWTConfig{PublicKeys: []string{pub}, RefreshURL: refreshSrv.URL, RefreshBefore: time.Minute})
	handler := am.Middleware(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		if r.Header.Get("X-User-ID") != "dave" {
			t.Fatalf("claims not refreshed")
		}
		w.WriteHeader(http.StatusOK)
	}))

	oldTok = newToken(t, priv, "old", "id5", time.Now().Add(10*time.Second))
	req := httptest.NewRequest(http.MethodGet, "/", nil)
	req.Header.Set("Authorization", "Bearer "+oldTok)
	resp := httptest.NewRecorder()
	handler.ServeHTTP(resp, req)
	if !refreshed {
		t.Fatal("refresh not called")
	}
	if resp.Code != http.StatusOK {
		t.Fatalf("expected 200 got %d", resp.Code)
	}
	if !srv.Exists("jwt:" + newTokStr) {
		t.Fatalf("refreshed token not cached")
	}
}

func TestAuthRateLimitPerUser(t *testing.T) {
	_, client := newRedis(t)
	priv, pub := genKeys(t)
	rl := NewRateLimiter(client, gwconfig.RateLimitSettings{PerUser: 1, Burst: 0})
	rl.SetWindow(time.Minute)
	am := newMiddleware(t, NewTokenCache(client), rl, JWTConfig{PublicKeys: []string{pub}})
	handler := am.Middleware(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) { w.WriteHeader(http.StatusOK) }))

	tok := newToken(t, priv, "eve", "id6", time.Now().Add(time.Minute))
	req := httptest.NewRequest(http.MethodGet, "/", nil)
	req.Header.Set("Authorization", "Bearer "+tok)
	resp := httptest.NewRecorder()
	handler.ServeHTTP(resp, req)
	if resp.Code != http.StatusOK {
		t.Fatalf("expected 200 got %d", resp.Code)
	}
	resp = httptest.NewRecorder()
	handler.ServeHTTP(resp, req)
	if resp.Code != http.StatusTooManyRequests {
		t.Fatalf("expected 429 got %d", resp.Code)
	}
}

func TestAuthCORSPreflight(t *testing.T) {
	_, client := newRedis(t)
	_, pub := genKeys(t)
	am := newMiddleware(t, NewTokenCache(client), nil, JWTConfig{PublicKeys: []string{pub}})
	handler := am.Middleware(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) { w.WriteHeader(http.StatusOK) }))

	req := httptest.NewRequest(http.MethodOptions, "/", nil)
	req.Header.Set("Access-Control-Request-Method", "GET")
	resp := httptest.NewRecorder()
	handler.ServeHTTP(resp, req)
	if resp.Code != http.StatusOK {
		t.Fatalf("expected 200 got %d", resp.Code)
	}
}
