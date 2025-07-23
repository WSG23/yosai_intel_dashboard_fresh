package middleware

import (
	"fmt"
	"net/http"
	"os"
	"strings"
	"time"

	"github.com/golang-jwt/jwt/v5"

	"github.com/WSG23/yosai-gateway/internal/auth"
)

// Auth middleware validates a JWT Authorization header.
func Auth(next http.Handler) http.Handler {
	secret := []byte(os.Getenv("JWT_SECRET"))
	return http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		authHdr := r.Header.Get("Authorization")
		if authHdr == "" {
			http.Error(w, "unauthorized", http.StatusUnauthorized)
			return
		}

		parts := strings.Fields(authHdr)
		if len(parts) != 2 || !strings.EqualFold(parts[0], "Bearer") {
			http.Error(w, "unauthorized", http.StatusUnauthorized)
			return
		}

		tokenStr := parts[1]
		claims := &auth.EnhancedClaims{}
		token, err := jwt.ParseWithClaims(tokenStr, claims, func(t *jwt.Token) (interface{}, error) {
			if _, ok := t.Method.(*jwt.SigningMethodHMAC); !ok {
				return nil, fmt.Errorf("unexpected signing method")
			}
			return secret, nil
		})
		if err != nil || !token.Valid {
			http.Error(w, "unauthorized", http.StatusUnauthorized)
			return
		}

		if claims.ExpiresAt != nil && claims.ExpiresAt.Before(time.Now()) {
			http.Error(w, "unauthorized", http.StatusUnauthorized)
			return
		}

		if claims.Issuer == "" {
			http.Error(w, "unauthorized", http.StatusUnauthorized)
			return
		}

		ctx := auth.NewContext(r.Context(), claims)
		next.ServeHTTP(w, r.WithContext(ctx))
	})
}
