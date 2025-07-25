package middleware

import (
	"fmt"
	"net/http"
	"strings"
	"time"

	"github.com/golang-jwt/jwt/v5"

	"github.com/WSG23/yosai-gateway/internal/auth"
	sharederrors "github.com/WSG23/yosai_intel_dashboard_fresh/shared/errors"
)

// Auth middleware validates a JWT Authorization header using the provided signing secret.
func Auth(secret []byte) func(http.Handler) http.Handler {
	return func(next http.Handler) http.Handler {
		return http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
			authHdr := r.Header.Get("Authorization")
			if authHdr == "" {
				sharederrors.WriteJSON(w, http.StatusUnauthorized, sharederrors.Unauthorized, "unauthorized", nil)
				return
			}

			parts := strings.Fields(authHdr)
			if len(parts) != 2 || !strings.EqualFold(parts[0], "Bearer") {
				sharederrors.WriteJSON(w, http.StatusUnauthorized, sharederrors.Unauthorized, "unauthorized", nil)
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
				sharederrors.WriteJSON(w, http.StatusUnauthorized, sharederrors.Unauthorized, "unauthorized", nil)
				return
			}

			if claims.ExpiresAt != nil && claims.ExpiresAt.Before(time.Now()) {
				sharederrors.WriteJSON(w, http.StatusUnauthorized, sharederrors.Unauthorized, "unauthorized", nil)
				return
			}

			if claims.Issuer == "" {
				sharederrors.WriteJSON(w, http.StatusUnauthorized, sharederrors.Unauthorized, "unauthorized", nil)
				return
			}

			ctx := auth.NewContext(r.Context(), claims)
			next.ServeHTTP(w, r.WithContext(ctx))
		})
	}
}
