package cache

import (
	"context"
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

	p := &CachePlugin{redis: client, rules: []CacheRule{{Path: "/foo", TTL: time.Minute}}}
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
	p := &CachePlugin{redis: client, rules: []CacheRule{rule}}
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
