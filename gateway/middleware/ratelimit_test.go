package middleware

import (
	"net/http"
	"net/http/httptest"
	"testing"

	"github.com/alicebob/miniredis/v2"
	"github.com/gorilla/mux"
	"github.com/redis/go-redis/v9"

	gwconfig "github.com/WSG23/yosai-gateway/internal/config"
)

func newLimiter(t *testing.T, cfg gwconfig.RateLimitSettings) *RateLimiter {
	srv, err := miniredis.Run()
	if err != nil {
		t.Fatalf("failed to start redis: %v", err)
	}
	t.Cleanup(srv.Close)
	client := redis.NewClient(&redis.Options{Addr: srv.Addr()})
	return NewRateLimiter(client, cfg)
}

func TestRateLimitBypassPaths(t *testing.T) {
	rl := newLimiter(t, gwconfig.RateLimitSettings{PerIP: 1, Burst: 0})
	r := mux.NewRouter()
	r.Use(rl.Middleware)
	r.HandleFunc("/health", func(w http.ResponseWriter, r *http.Request) { w.WriteHeader(http.StatusOK) })
	r.HandleFunc("/", func(w http.ResponseWriter, r *http.Request) { w.WriteHeader(http.StatusOK) })

	req := httptest.NewRequest(http.MethodGet, "/", nil)
	resp := httptest.NewRecorder()
	r.ServeHTTP(resp, req)
	resp = httptest.NewRecorder()
	r.ServeHTTP(resp, req)
	if resp.Code != http.StatusTooManyRequests {
		t.Fatalf("expected 429 got %d", resp.Code)
	}
	hreq := httptest.NewRequest(http.MethodGet, "/health", nil)
	hresp := httptest.NewRecorder()
	r.ServeHTTP(hresp, hreq)
	if hresp.Code != http.StatusOK {
		t.Fatalf("health not bypassed")
	}
}

func TestRateLimitHeaders(t *testing.T) {
	rl := newLimiter(t, gwconfig.RateLimitSettings{PerIP: 2, Burst: 1})
	r := mux.NewRouter()
	r.Use(rl.Middleware)
	r.HandleFunc("/", func(w http.ResponseWriter, r *http.Request) { w.WriteHeader(http.StatusOK) })

	req := httptest.NewRequest(http.MethodGet, "/", nil)
	resp := httptest.NewRecorder()
	r.ServeHTTP(resp, req)
	if resp.Header().Get("X-RateLimit-Limit") == "" {
		t.Fatalf("missing limit header")
	}
	if resp.Header().Get("X-RateLimit-Remaining") != "2" {
		t.Fatalf("expected remaining 2 got %s", resp.Header().Get("X-RateLimit-Remaining"))
	}
}
