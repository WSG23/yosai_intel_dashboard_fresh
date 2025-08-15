package cache

import (
	"context"
	"encoding/json"
	"net/http"
	"net/http/httptest"
	"testing"
	"time"

	"github.com/alicebob/miniredis/v2"
	"github.com/redis/go-redis/v9"
)

func newTestRedis(t *testing.T) (*miniredis.Miniredis, *redis.Client) {
	srv, err := miniredis.Run()
	if err != nil {
		t.Fatalf("failed to start miniredis: %v", err)
	}
	client := redis.NewClient(&redis.Options{Addr: srv.Addr()})
	return srv, client
}

func TestAPICacheGET(t *testing.T) {
	srv, client := newTestRedis(t)
	defer srv.Close()

	p := NewCachePlugin(client, []CacheRule{{Path: "/foo", TTL: time.Minute}})
	handler := http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		w.WriteHeader(http.StatusOK)
		w.Write([]byte("ok"))
	})

	w1 := httptest.NewRecorder()
	req := httptest.NewRequest(http.MethodGet, "/foo", nil)
	p.Process(context.Background(), req, w1, handler)
	if w1.Header().Get("X-Cache") != "MISS" {
		t.Fatalf("expected MISS got %s", w1.Header().Get("X-Cache"))
	}

	w2 := httptest.NewRecorder()
	p.Process(context.Background(), req, w2, handler)
	if w2.Header().Get("X-Cache") != "HIT" {
		t.Fatalf("expected HIT got %s", w2.Header().Get("X-Cache"))
	}
}

func TestAPICacheHeadAndInvalidate(t *testing.T) {
	srv, client := newTestRedis(t)
	defer srv.Close()

	rule := CacheRule{
		Path:            "/foo",
		TTL:             time.Minute,
		InvalidatePaths: []string{"/invalidate"},
	}
	p := NewCachePlugin(client, []CacheRule{rule})
	handler := http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		w.WriteHeader(http.StatusOK)
		w.Write([]byte("ok"))
	})

	// cache using HEAD
	reqHead := httptest.NewRequest(http.MethodHead, "/foo", nil)
	w1 := httptest.NewRecorder()
	p.Process(context.Background(), reqHead, w1, handler)

	// second HEAD should hit cache
	w2 := httptest.NewRecorder()
	p.Process(context.Background(), reqHead, w2, handler)
	if w2.Header().Get("X-Cache") != "HIT" {
		t.Fatalf("expected HIT got %s", w2.Header().Get("X-Cache"))
	}

	// invalidate via POST
	inval := httptest.NewRequest(http.MethodPost, "/invalidate", nil)
	w3 := httptest.NewRecorder()
	p.Process(context.Background(), inval, w3, handler)

	// GET after invalidation should miss
	reqGet := httptest.NewRequest(http.MethodGet, "/foo", nil)
	w4 := httptest.NewRecorder()
	p.Process(context.Background(), reqGet, w4, handler)
	if w4.Header().Get("X-Cache") != "MISS" {
		t.Fatalf("expected MISS after invalidate got %s", w4.Header().Get("X-Cache"))
	}
}

func TestAPICacheFallback(t *testing.T) {
	srv, client := newTestRedis(t)
	defer srv.Close()

	rule := CacheRule{Path: "/foo", TTL: time.Minute}
	p := NewCachePlugin(client, []CacheRule{rule})

	req := httptest.NewRequest(http.MethodGet, "/foo", nil)
	key := cacheKey(req, rule)
	data, _ := json.Marshal(cachedResponse{StatusCode: http.StatusOK, Headers: http.Header{"Content-Type": {"text/plain"}}, Body: []byte("cached")})
	client.Set(context.Background(), key, data, time.Minute)

	handler := http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		w.WriteHeader(http.StatusInternalServerError)
	})

	w := httptest.NewRecorder()
	p.Process(context.Background(), req, w, handler)
	if w.Header().Get("X-Cache") != "STALE" {
		t.Fatalf("expected STALE got %s", w.Header().Get("X-Cache"))
	}
	if w.Code != http.StatusOK || w.Body.String() != "cached" {
		t.Fatalf("unexpected fallback response: %d %s", w.Code, w.Body.String())
	}
}

func TestAPICacheFallbackEmpty(t *testing.T) {
	srv, client := newTestRedis(t)
	defer srv.Close()

	rule := CacheRule{Path: "/foo", TTL: time.Minute}
	p := NewCachePlugin(client, []CacheRule{rule})

	handler := http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		w.WriteHeader(http.StatusInternalServerError)
	})

	req := httptest.NewRequest(http.MethodGet, "/foo", nil)
	w := httptest.NewRecorder()
	p.Process(context.Background(), req, w, handler)
	if w.Header().Get("X-Cache") != "EMPTY" {
		t.Fatalf("expected EMPTY got %s", w.Header().Get("X-Cache"))
	}
	if w.Code != http.StatusOK || w.Body.String() != "{}" {
		t.Fatalf("unexpected empty fallback: %d %s", w.Code, w.Body.String())
	}
}
