package middleware

import (
    "context"
    "net/http"
    "strings"

    "github.com/WSG23/yosai-gateway/internal/auth"
)

func Authentication(next http.Handler) http.Handler {
    return http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
        // Skip auth for health check
        if r.URL.Path == "/health" {
            next.ServeHTTP(w, r)
            return
        }

        // Extract token
        authHeader := r.Header.Get("Authorization")
        if authHeader == "" {
            next.ServeHTTP(w, r)
            return
        }

        parts := strings.Split(authHeader, " ")
        if len(parts) != 2 || parts[0] != "Bearer" {
            http.Error(w, "Invalid authorization header", http.StatusUnauthorized)
            return
        }

        // Validate token
        claims, err := auth.ValidateToken(parts[1])
        if err != nil {
            http.Error(w, "Invalid token", http.StatusUnauthorized)
            return
        }

        // Add claims to context
        ctx := context.WithValue(r.Context(), "user", claims)
        next.ServeHTTP(w, r.WithContext(ctx))
    })
}

func RequireAuth(next http.Handler) http.Handler {
    return http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
        user := r.Context().Value("user")
        if user == nil {
            http.Error(w, "Authentication required", http.StatusUnauthorized)
            return
        }
        next.ServeHTTP(w, r)
    })
}
