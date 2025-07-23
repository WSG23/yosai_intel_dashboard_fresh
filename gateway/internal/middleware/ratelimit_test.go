package middleware

import (
	"net/http"
	"net/http/httptest"
	"testing"
	"time"

	"github.com/gorilla/mux"
)

func TestRateLimitDeniesWithoutTokens(t *testing.T) {
	r := mux.NewRouter()
	r.Use(RateLimit)
	r.HandleFunc("/", func(w http.ResponseWriter, r *http.Request) { w.WriteHeader(http.StatusOK) })

	req := httptest.NewRequest(http.MethodGet, "/", nil)
	resp := httptest.NewRecorder()
	r.ServeHTTP(resp, req)
	if resp.Code != http.StatusTooManyRequests {
		t.Fatalf("expected 429 got %d", resp.Code)
	}
}

func TestRateLimitCustomSettings(t *testing.T) {
	t.Setenv("RATE_LIMIT_BUCKET", "1")
	t.Setenv("RATE_LIMIT_INTERVAL_MS", "50")

	handler := RateLimit(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) { w.WriteHeader(http.StatusOK) }))

	req := httptest.NewRequest(http.MethodGet, "/", nil)

	resp1 := httptest.NewRecorder()
	handler.ServeHTTP(resp1, req)
	if resp1.Code != http.StatusTooManyRequests {
		t.Fatalf("expected 429 got %d", resp1.Code)
	}

	time.Sleep(60 * time.Millisecond)

	resp2 := httptest.NewRecorder()
	handler.ServeHTTP(resp2, req)
	if resp2.Code != http.StatusOK {
		t.Fatalf("expected 200 got %d", resp2.Code)
	}
}
