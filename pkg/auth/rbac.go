package auth

import (
	_ "embed"
	"gopkg.in/yaml.v3"
	"strings"
	"sync"
)

//go:embed rbac.yaml
var rbacConfig []byte

type config struct {
	Roles  map[string][]string `yaml:"roles"`
	Routes map[string]string   `yaml:"routes"`
}

var (
	loadOnce   sync.Once
	rolePerms  map[string][]string
	routePerms map[string]string
)

func load() {
	var cfg config
	if err := yaml.Unmarshal(rbacConfig, &cfg); err != nil {
		rolePerms = map[string][]string{}
		routePerms = map[string]string{}
		return
	}
	rolePerms = cfg.Roles
	routePerms = cfg.Routes
}

// RolesHavePermission returns true if any role grants perm.
func RolesHavePermission(roles []string, perm string) bool {
	loadOnce.Do(load)
	for _, r := range roles {
		if perms, ok := rolePerms[r]; ok {
			for _, p := range perms {
				if p == perm {
					return true
				}
			}
		}
	}
	return false
}

// HasRouteAccess returns true if the given roles or explicit permissions allow access to path.
func HasRouteAccess(roles, perms []string, path string) bool {
	loadOnce.Do(load)
	perm, ok := PermissionForRoute(path)
	if !ok {
		return true
	}
	for _, p := range perms {
		if strings.TrimSpace(p) == perm {
			return true
		}
	}
	return RolesHavePermission(roles, perm)
}

// PermissionForRoute returns the permission configured for a path.
func PermissionForRoute(path string) (string, bool) {
	for prefix, perm := range routePerms {
		if strings.HasPrefix(path, prefix) {
			return perm, true
		}
	}
	return "", false
}
