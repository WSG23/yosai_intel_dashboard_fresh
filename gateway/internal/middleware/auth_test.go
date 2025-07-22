package middleware

import (
    "net/http"
    "net/http/httptest"
    "os"
    "testing"
    "time"

    "github.com/golang-jwt/jwt/v5"
)

func TestAuthMiddlewareSuccessAndFailure(t *testing.T) {
    os.Setenv("JWT_SECRET", "test")
    h := Auth(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
        w.WriteHeader(http.StatusOK)
    }))

    // missing header
    req := httptest.NewRequest(http.MethodGet, "/", nil)
    resp := httptest.NewRecorder()
    h.ServeHTTP(resp, req)
    if resp.Code != http.StatusUnauthorized {
        t.Fatalf("expected 401 got %d", resp.Code)
    }

    // valid token
    token := jwt.NewWithClaims(jwt.SigningMethodHS256, jwt.MapClaims{
        "sub": "svc",
        "exp": time.Now().Add(time.Minute).Unix(),
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
    os.Setenv("JWT_SECRET", "test")
    h := Auth(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
        w.WriteHeader(http.StatusOK)
    }))
    token := jwt.NewWithClaims(jwt.SigningMethodHS256, jwt.MapClaims{
        "sub": "svc",
        "exp": time.Now().Add(-time.Minute).Unix(),
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
}
