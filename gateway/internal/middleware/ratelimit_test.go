package middleware

import (
    "net/http"
    "net/http/httptest"
    "testing"

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
