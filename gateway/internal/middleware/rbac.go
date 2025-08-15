package middleware

import (
	"net/http"

	authz "github.com/WSG23/auth"
	"github.com/WSG23/yosai-gateway/internal/auth"
        "github.com/WSG23/yosai-gateway/internal/rbac"
        xerrors "github.com/WSG23/errors"
)

// RequirePermission checks that the request's subject has the given permission.
func RequirePermission(s *rbac.RBACService, perm string) func(http.Handler) http.Handler {
	return func(next http.Handler) http.Handler {
		return http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
			claims, ok := auth.FromContext(r.Context())
			if !ok {
                                xerrors.WriteJSON(w, http.StatusForbidden, xerrors.Unauthorized, "forbidden", nil)
				return
			}
			if claims.Subject == "" {
                                xerrors.WriteJSON(w, http.StatusForbidden, xerrors.Unauthorized, "forbidden", nil)
				return
			}
			for _, p := range claims.Permissions {
				if p == perm {
					next.ServeHTTP(w, r)
					return
				}
			}
			if authz.RolesHavePermission(claims.Roles, perm) {
				next.ServeHTTP(w, r)
				return
			}
			if s != nil {
				allowed, err := s.HasPermission(r.Context(), claims.Subject, perm)
				if err == nil && allowed {
					next.ServeHTTP(w, r)
					return
				}
			}
                        xerrors.WriteJSON(w, http.StatusForbidden, xerrors.Unauthorized, "forbidden", nil)
		})
	}
}

// RequireRole checks that the request's claims include the given role.
func RequireRole(role string) func(http.Handler) http.Handler {
	return func(next http.Handler) http.Handler {
		return http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
			claims, ok := auth.FromContext(r.Context())
			if !ok {
                                xerrors.WriteJSON(w, http.StatusForbidden, xerrors.Unauthorized, "forbidden", nil)
				return
			}
			for _, rle := range claims.Roles {
				if rle == role {
					next.ServeHTTP(w, r)
					return
				}
			}
                        xerrors.WriteJSON(w, http.StatusForbidden, xerrors.Unauthorized, "forbidden", nil)
		})
	}
}

// RequireRoutePermission checks roles and permissions against configured routes.
func RequireRoutePermission(s *rbac.RBACService) func(http.Handler) http.Handler {
	return func(next http.Handler) http.Handler {
		return http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
			claims, ok := auth.FromContext(r.Context())
			if !ok {
				sharederrors.WriteJSON(w, http.StatusForbidden, sharederrors.Unauthorized, "forbidden", nil)
				return
			}
			if authz.HasRouteAccess(claims.Roles, claims.Permissions, r.URL.Path) {
				next.ServeHTTP(w, r)
				return
			}
			if s != nil {
				perm, ok := authz.PermissionForRoute(r.URL.Path)
				if ok {
					allowed, err := s.HasPermission(r.Context(), claims.Subject, perm)
					if err == nil && allowed {
						next.ServeHTTP(w, r)
						return
					}
				}
			}
			sharederrors.WriteJSON(w, http.StatusForbidden, sharederrors.Unauthorized, "forbidden", nil)
		})
	}
}
