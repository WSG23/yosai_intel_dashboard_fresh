package ratelimit

import (
	"net/http"
	"net/http/httptest"
	"testing"
)

func TestRateLimitPlugin(t *testing.T) {
	p := &RateLimitPlugin{rules: []RateLimitRule{{Path: "/", LimitPerMin: 1, Burst: 1}}}
	handler := http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) { w.WriteHeader(http.StatusOK) })

	w1 := httptest.NewRecorder()
	p.Process(nil, httptest.NewRequest("GET", "/", nil), w1, handler)
	if w1.Code != http.StatusOK {
		t.Fatalf("expected 200 got %d", w1.Code)
	}

	w2 := httptest.NewRecorder()
	p.Process(nil, httptest.NewRequest("GET", "/", nil), w2, handler)
	if w2.Code != http.StatusTooManyRequests {
		t.Fatalf("expected 429 got %d", w2.Code)
	}
}
