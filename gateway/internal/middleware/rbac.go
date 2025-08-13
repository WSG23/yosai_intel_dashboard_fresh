package middleware

import (
	"net/http"

	"github.com/WSG23/yosai-gateway/internal/auth"
	"github.com/WSG23/yosai-gateway/internal/rbac"
	sharederrors "github.com/WSG23/yosai_intel_dashboard_fresh/shared/errors"
)

// RequirePermission checks that the request's subject has the given permission.
func RequirePermission(s *rbac.RBACService, perm string) func(http.Handler) http.Handler {
	return func(next http.Handler) http.Handler {
		return http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
			claims, ok := auth.FromContext(r.Context())
			if !ok {
				sharederrors.WriteJSON(w, http.StatusForbidden, sharederrors.Unauthorized, "forbidden", nil)
				return
			}
			if claims.Subject == "" {
				sharederrors.WriteJSON(w, http.StatusForbidden, sharederrors.Unauthorized, "forbidden", nil)
				return
			}
			allowed, err := s.HasPermission(r.Context(), claims.Subject, perm)
			if err != nil || !allowed {
				sharederrors.WriteJSON(w, http.StatusForbidden, sharederrors.Unauthorized, "forbidden", nil)
				return
			}
			next.ServeHTTP(w, r)
		})
	}
}

// RequireRole checks that the request's claims include the given role.
func RequireRole(role string) func(http.Handler) http.Handler {
	return func(next http.Handler) http.Handler {
		return http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
			claims, ok := auth.FromContext(r.Context())
			if !ok {
				sharederrors.WriteJSON(w, http.StatusForbidden, sharederrors.Unauthorized, "forbidden", nil)
				return
			}
			for _, rle := range claims.Roles {
				if rle == role {
					next.ServeHTTP(w, r)
					return
				}
			}
			sharederrors.WriteJSON(w, http.StatusForbidden, sharederrors.Unauthorized, "forbidden", nil)
		})
	}
}
