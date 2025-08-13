package middleware

import (
	"net/http"
	"net/http/httptest"
	"testing"
	"time"

	"github.com/golang-jwt/jwt/v5"

	"github.com/WSG23/yosai-gateway/internal/auth"
	"github.com/WSG23/yosai-gateway/internal/rbac"
)

func TestRequirePermission(t *testing.T) {
	t.Setenv("PERMISSIONS_ALICE", "read")
	svc := rbac.New(time.Minute)

	h := RequirePermission(svc, "read")(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		w.WriteHeader(http.StatusOK)
	}))

	claims := &auth.EnhancedClaims{RegisteredClaims: jwt.RegisteredClaims{Subject: "alice"}}
	req := httptest.NewRequest(http.MethodGet, "/", nil)
	req = req.WithContext(auth.NewContext(req.Context(), claims))
	resp := httptest.NewRecorder()
	h.ServeHTTP(resp, req)
	if resp.Code != http.StatusOK {
		t.Fatalf("expected 200 got %d", resp.Code)
	}

	h = RequirePermission(svc, "write")(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		w.WriteHeader(http.StatusOK)
	}))
	resp = httptest.NewRecorder()
	h.ServeHTTP(resp, req)
	if resp.Code != http.StatusForbidden {
		t.Fatalf("expected 403 got %d", resp.Code)
	}
}

func TestRequireRole(t *testing.T) {
	h := RequireRole("admin")(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		w.WriteHeader(http.StatusOK)
	}))

	claims := &auth.EnhancedClaims{Roles: []string{"admin"}}
	req := httptest.NewRequest(http.MethodGet, "/", nil)
	req = req.WithContext(auth.NewContext(req.Context(), claims))
	resp := httptest.NewRecorder()
	h.ServeHTTP(resp, req)
	if resp.Code != http.StatusOK {
		t.Fatalf("expected 200 got %d", resp.Code)
	}

	claims = &auth.EnhancedClaims{Roles: []string{"user"}}
	req = httptest.NewRequest(http.MethodGet, "/", nil)
	req = req.WithContext(auth.NewContext(req.Context(), claims))
	resp = httptest.NewRecorder()
	h.ServeHTTP(resp, req)
	if resp.Code != http.StatusForbidden {
		t.Fatalf("expected 403 got %d", resp.Code)
	}
}
