package middleware

import (
	"net/http"

	"github.com/WSG23/yosai-gateway/internal/auth"
	"github.com/WSG23/yosai-gateway/internal/rbac"
)

// RequirePermission checks that the request's subject has the given permission.
func RequirePermission(s *rbac.RBACService, perm string) func(http.Handler) http.Handler {
	return func(next http.Handler) http.Handler {
		return http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
			claims, ok := auth.FromContext(r.Context())
			if !ok {
				http.Error(w, "forbidden", http.StatusForbidden)
				return
			}
			if claims.Subject == "" {
				http.Error(w, "forbidden", http.StatusForbidden)
				return
			}
			allowed, err := s.HasPermission(r.Context(), claims.Subject, perm)
			if err != nil || !allowed {
				http.Error(w, "forbidden", http.StatusForbidden)
				return
			}
			next.ServeHTTP(w, r)
		})
	}
}
