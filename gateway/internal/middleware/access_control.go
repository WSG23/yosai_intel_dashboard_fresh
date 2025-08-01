package middleware

import (
	"net/http"
	"strings"

	sharederrors "github.com/WSG23/yosai_intel_dashboard_fresh/shared/errors"
)

// RequirePermission checks the X-Permissions header for a permission value.
func RequirePermissionHeader(perm string) func(http.Handler) http.Handler {
	return func(next http.Handler) http.Handler {
		return http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
			perms := strings.Split(r.Header.Get("X-Permissions"), ",")
			for _, p := range perms {
				if strings.TrimSpace(p) == perm {
					next.ServeHTTP(w, r)
					return
				}
			}
			sharederrors.WriteJSON(w, http.StatusForbidden, sharederrors.Unauthorized, "forbidden", nil)
		})
	}
}

// RequireRole checks the X-Roles header for a role value.
func RequireRoleHeader(role string) func(http.Handler) http.Handler {
	return func(next http.Handler) http.Handler {
		return http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
			roles := strings.Split(r.Header.Get("X-Roles"), ",")
			for _, rle := range roles {
				if strings.TrimSpace(rle) == role {
					next.ServeHTTP(w, r)
					return
				}
			}
			sharederrors.WriteJSON(w, http.StatusForbidden, sharederrors.Unauthorized, "forbidden", nil)
		})
	}
}
