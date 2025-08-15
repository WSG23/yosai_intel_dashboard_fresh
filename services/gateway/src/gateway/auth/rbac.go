package auth

// RolePermissions defines the permissions available for each role.
// This allows the gateway to resolve a subject's capabilities without
// a backing store when running in simple deployments or tests.
var RolePermissions = map[string][]string{
	"admin": {
		"users:read",
		"users:write",
		"analytics:read",
		"config:write",
	},
	"analyst": {
		"analytics:read",
		"analytics:write",
	},
	"viewer": {
		"analytics:read",
	},
	"service": {
		"tasks:enqueue",
		"tasks:dequeue",
	},
}

// Roles provides a sorted list of known roles.
// It can be used by CLI utilities or documentation generators.
var Roles = func() []string {
	keys := make([]string, 0, len(RolePermissions))
	for k := range RolePermissions {
		keys = append(keys, k)
	}
	// simple insertion sort as the slice is tiny
	for i := 1; i < len(keys); i++ {
		for j := i; j > 0 && keys[j-1] > keys[j]; j-- {
			keys[j-1], keys[j] = keys[j], keys[j-1]
		}
	}
	return keys
}()

// PermissionsFor returns the permission list for the given role.
func PermissionsFor(role string) []string {
	perms, ok := RolePermissions[role]
	if !ok {
		return nil
	}
	cp := make([]string, len(perms))
	copy(cp, perms)
	return cp
}
