package middleware

import (
        "encoding/json"
        "net/http"
        "net/http/httptest"
        "testing"

        "github.com/alicebob/miniredis/v2"
        "github.com/gorilla/mux"
        "github.com/redis/go-redis/v9"

        gwconfig "github.com/WSG23/yosai-gateway/internal/config"
        serrors "github.com/WSG23/errors"
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

func TestRateLimitPerUser(t *testing.T) {
        rl := newLimiter(t, gwconfig.RateLimitSettings{PerUser: 1, Burst: 0})
        r := mux.NewRouter()
        r.Use(rl.Middleware)
        r.HandleFunc("/", func(w http.ResponseWriter, r *http.Request) { w.WriteHeader(http.StatusOK) })

        req := httptest.NewRequest(http.MethodGet, "/", nil)
        req.Header.Set("X-User-ID", "alice")
        resp := httptest.NewRecorder()
        r.ServeHTTP(resp, req)
        if resp.Code != http.StatusOK {
                t.Fatalf("expected 200 got %d", resp.Code)
        }

        req2 := httptest.NewRequest(http.MethodGet, "/", nil)
        req2.Header.Set("X-User-ID", "alice")
        resp2 := httptest.NewRecorder()
        r.ServeHTTP(resp2, req2)
        if resp2.Code != http.StatusTooManyRequests {
                t.Fatalf("expected 429 got %d", resp2.Code)
        }

        req3 := httptest.NewRequest(http.MethodGet, "/", nil)
        req3.Header.Set("X-User-ID", "bob")
        resp3 := httptest.NewRecorder()
        r.ServeHTTP(resp3, req3)
        if resp3.Code != http.StatusOK {
                t.Fatalf("user-specific limit not applied")
        }
}

func TestRateLimitErrorFormat(t *testing.T) {
        rl := newLimiter(t, gwconfig.RateLimitSettings{PerIP: 1, Burst: 0})
        r := mux.NewRouter()
        r.Use(rl.Middleware)
        r.HandleFunc("/", func(w http.ResponseWriter, r *http.Request) { w.WriteHeader(http.StatusOK) })

        req := httptest.NewRequest(http.MethodGet, "/", nil)
        resp := httptest.NewRecorder()
        r.ServeHTTP(resp, req)
        resp = httptest.NewRecorder()
        r.ServeHTTP(resp, req)
        if resp.Code != http.StatusTooManyRequests {
                t.Fatalf("expected 429 got %d", resp.Code)
        }
        var e serrors.Error
        if err := json.NewDecoder(resp.Body).Decode(&e); err != nil {
                t.Fatalf("decode: %v", err)
        }
        if e.Code != serrors.Unavailable || e.Message != "rate limit exceeded" {
                t.Fatalf("unexpected error: %+v", e)
        }
}
