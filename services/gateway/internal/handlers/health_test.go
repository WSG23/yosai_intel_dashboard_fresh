package handlers

import (
	"net/http"
	"net/http/httptest"
	"testing"
	"time"

	"github.com/golang-jwt/jwt/v5"
	"github.com/gorilla/mux"

	"github.com/WSG23/yosai-gateway/internal/middleware"
)

func setupRouter(secret []byte) *mux.Router {
	r := mux.NewRouter()
	r.HandleFunc("/health", HealthCheck).Methods(http.MethodGet)
	r.Use(middleware.Auth(secret))
	return r
}

func TestHealthUnauthorized(t *testing.T) {
	r := setupRouter([]byte("test"))

	req := httptest.NewRequest(http.MethodGet, "/health", nil)
	resp := httptest.NewRecorder()
	r.ServeHTTP(resp, req)

	if resp.Code != http.StatusUnauthorized {
		t.Fatalf("expected 401, got %d", resp.Code)
	}
}

func TestHealthAuthorized(t *testing.T) {
	secret := []byte("test")
	r := setupRouter(secret)

	token := jwt.NewWithClaims(jwt.SigningMethodHS256, jwt.MapClaims{
		"sub": "svc",
		"iss": "gateway",
		"exp": time.Now().Add(time.Minute).Unix(),
	})
	signed, err := token.SignedString(secret)
	if err != nil {
		t.Fatal(err)
	}

	req := httptest.NewRequest(http.MethodGet, "/health", nil)
	req.Header.Set("Authorization", "Bearer "+signed)
	resp := httptest.NewRecorder()
	r.ServeHTTP(resp, req)

	if resp.Code != http.StatusOK {
		t.Fatalf("expected 200, got %d", resp.Code)
	}
}
