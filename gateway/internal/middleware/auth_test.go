package middleware

import (
	"encoding/json"
	"net/http"
	"net/http/httptest"
	"testing"
	"time"

	"github.com/golang-jwt/jwt/v5"

	"github.com/WSG23/yosai-gateway/internal/auth"
)

func TestAuthMiddlewareSuccessAndFailure(t *testing.T) {
	h := Auth([]byte("test"))(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		w.WriteHeader(http.StatusOK)
	}))

	// missing header
	req := httptest.NewRequest(http.MethodGet, "/", nil)
	resp := httptest.NewRecorder()
	h.ServeHTTP(resp, req)
	if resp.Code != http.StatusUnauthorized {
		t.Fatalf("expected 401 got %d", resp.Code)
	}
	var e struct {
		Details map[string]string `json:"details"`
	}
	_ = json.NewDecoder(resp.Body).Decode(&e)
	if e.Details["reason"] != "missing" {
		t.Fatalf("expected missing reason got %v", e.Details["reason"])
	}

	// valid token
	token := jwt.NewWithClaims(jwt.SigningMethodHS256, &auth.EnhancedClaims{
		RegisteredClaims: jwt.RegisteredClaims{
			Subject:   "svc",
			Issuer:    "gateway",
			ExpiresAt: jwt.NewNumericDate(time.Now().Add(time.Minute)),
		},
	})
	signed, err := token.SignedString([]byte("test"))
	if err != nil {
		t.Fatal(err)
	}
	req = httptest.NewRequest(http.MethodGet, "/", nil)
	req.Header.Set("Authorization", "Bearer "+signed)
	resp = httptest.NewRecorder()
	h.ServeHTTP(resp, req)
	if resp.Code != http.StatusOK {
		t.Fatalf("expected 200 got %d", resp.Code)
	}
}

func TestAuthMiddlewareExpired(t *testing.T) {
	h := Auth([]byte("test"))(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		w.WriteHeader(http.StatusOK)
	}))
	token := jwt.NewWithClaims(jwt.SigningMethodHS256, &auth.EnhancedClaims{
		RegisteredClaims: jwt.RegisteredClaims{
			Subject:   "svc",
			Issuer:    "gateway",
			ExpiresAt: jwt.NewNumericDate(time.Now().Add(-time.Minute)),
		},
	})
	signed, err := token.SignedString([]byte("test"))
	if err != nil {
		t.Fatal(err)
	}
	req := httptest.NewRequest(http.MethodGet, "/", nil)
	req.Header.Set("Authorization", "Bearer "+signed)
	resp := httptest.NewRecorder()
	h.ServeHTTP(resp, req)
	if resp.Code != http.StatusUnauthorized {
		t.Fatalf("expected 401 got %d", resp.Code)
	}
	var e struct {
		Details map[string]string `json:"details"`
	}
	_ = json.NewDecoder(resp.Body).Decode(&e)
	if e.Details["reason"] != "expired" {
		t.Fatalf("expected expired reason got %v", e.Details["reason"])
	}
}
