package middleware

import (
	"net/http"
	"net/http/httptest"
	"testing"
)

func TestSecurityHeaders(t *testing.T) {
	h := SecurityHeaders()(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		w.WriteHeader(http.StatusOK)
	}))

	req := httptest.NewRequest(http.MethodGet, "/", nil)
	resp := httptest.NewRecorder()
	h.ServeHTTP(resp, req)

	if resp.Header().Get("Content-Security-Policy") == "" {
		t.Fatal("missing Content-Security-Policy")
	}
	if resp.Header().Get("X-Frame-Options") != "DENY" {
		t.Fatalf("unexpected X-Frame-Options: %s", resp.Header().Get("X-Frame-Options"))
	}
	if resp.Header().Get("X-Content-Type-Options") != "nosniff" {
		t.Fatalf("unexpected X-Content-Type-Options: %s", resp.Header().Get("X-Content-Type-Options"))
	}
}
