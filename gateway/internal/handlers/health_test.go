package handlers

import (
	"net/http"
	"net/http/httptest"
	"os"
	"testing"
	"time"

	"github.com/golang-jwt/jwt/v5"
	"github.com/gorilla/mux"

	"github.com/WSG23/yosai-gateway/internal/middleware"
)

func setupRouter() *mux.Router {
	r := mux.NewRouter()
	r.HandleFunc("/health", HealthCheck).Methods(http.MethodGet)
	r.Use(middleware.Auth)
	return r
}

func TestHealthUnauthorized(t *testing.T) {
	os.Setenv("JWT_SECRET", "test")
	r := setupRouter()

	req := httptest.NewRequest(http.MethodGet, "/health", nil)
	resp := httptest.NewRecorder()
	r.ServeHTTP(resp, req)

	if resp.Code != http.StatusUnauthorized {
		t.Fatalf("expected 401, got %d", resp.Code)
	}
}

func TestHealthAuthorized(t *testing.T) {
	secret := []byte("test")
	os.Setenv("JWT_SECRET", string(secret))
	r := setupRouter()

	token := jwt.NewWithClaims(jwt.SigningMethodHS256, jwt.MapClaims{
		"sub": "svc",
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
