package auth

import (
	_ "embed"
	"gopkg.in/yaml.v3"
	"sync"
)

//go:embed rbac.yaml
var rbacConfig []byte

type config struct {
	Roles map[string][]string `yaml:"roles"`
}

var (
	loadOnce  sync.Once
	rolePerms map[string][]string
)

func load() {
	var cfg config
	if err := yaml.Unmarshal(rbacConfig, &cfg); err != nil {
		rolePerms = map[string][]string{}
		return
	}
	rolePerms = cfg.Roles
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
