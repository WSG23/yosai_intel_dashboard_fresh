package middleware

import (
	"net/http"
	"strings"
)

// RequirePermission checks the X-Permissions header for a permission value.
func RequirePermission(perm string) func(http.Handler) http.Handler {
	return func(next http.Handler) http.Handler {
		return http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
			perms := strings.Split(r.Header.Get("X-Permissions"), ",")
			for _, p := range perms {
				if strings.TrimSpace(p) == perm {
					next.ServeHTTP(w, r)
					return
				}
			}
			http.Error(w, "forbidden", http.StatusForbidden)
		})
	}
}

// RequireRole checks the X-Roles header for a role value.
func RequireRole(role string) func(http.Handler) http.Handler {
	return func(next http.Handler) http.Handler {
		return http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
			roles := strings.Split(r.Header.Get("X-Roles"), ",")
			for _, rle := range roles {
				if strings.TrimSpace(rle) == role {
					next.ServeHTTP(w, r)
					return
				}
			}
			http.Error(w, "forbidden", http.StatusForbidden)
		})
	}
}
