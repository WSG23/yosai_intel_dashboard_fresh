package middleware

import (
	"errors"
	"net/http"
	"strings"
	"time"

	"github.com/golang-jwt/jwt/v5"

	xerrors "github.com/WSG23/errors"

        "github.com/WSG23/yosai-gateway/internal/auth"
        xerrors "github.com/WSG23/errors"
)

func reasonFromError(err error) string {
	switch {
	case errors.Is(err, jwt.ErrTokenExpired):
		return "expired"
	case errors.Is(err, jwt.ErrTokenInvalidAudience):
		return "invalid_aud"
	case errors.Is(err, jwt.ErrTokenSignatureInvalid):
		return "invalid_signature"
	case errors.Is(err, jwt.ErrTokenNotValidYet):
		return "not_yet_valid"
	case errors.Is(err, jwt.ErrTokenInvalidIssuer):
		return "invalid_iss"
	case errors.Is(err, jwt.ErrTokenMalformed):
		return "malformed"
	default:
		return "invalid"
	}
}

// Auth middleware validates a JWT Authorization header using the provided signing secret.
func Auth(secret []byte) func(http.Handler) http.Handler {
	return func(next http.Handler) http.Handler {
		return http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
			authHdr := r.Header.Get("Authorization")
			if authHdr == "" {
                                xerrors.WriteJSON(w, http.StatusUnauthorized, xerrors.Unauthorized, "unauthorized", map[string]string{"reason": "missing"})
				return
			}

			parts := strings.Fields(authHdr)
			if len(parts) != 2 || !strings.EqualFold(parts[0], "Bearer") {
                                xerrors.WriteJSON(w, http.StatusUnauthorized, xerrors.Unauthorized, "unauthorized", map[string]string{"reason": "invalid_header"})
				return
			}

			tokenStr := parts[1]
			claims := &auth.EnhancedClaims{}
			token, err := jwt.ParseWithClaims(tokenStr, claims, func(t *jwt.Token) (interface{}, error) {
				if _, ok := t.Method.(*jwt.SigningMethodHMAC); !ok {
					return nil, xerrors.Errorf("unexpected signing method")
				}
				return secret, nil
			})
			if err != nil || !token.Valid {
                                xerrors.WriteJSON(w, http.StatusUnauthorized, xerrors.Unauthorized, "unauthorized", map[string]string{"reason": reasonFromError(err)})
				return
			}

			if claims.ExpiresAt != nil && claims.ExpiresAt.Before(time.Now()) {
				sharederrors.WriteJSON(w, http.StatusUnauthorized, sharederrors.Unauthorized, "unauthorized", map[string]string{"reason": "expired"})
				return
			}

			if claims.Issuer == "" {
				sharederrors.WriteJSON(w, http.StatusUnauthorized, sharederrors.Unauthorized, "unauthorized", map[string]string{"reason": "invalid_iss"})
				return
			}

			ctx := auth.NewContext(r.Context(), claims)
			next.ServeHTTP(w, r.WithContext(ctx))
		})
	}
}
