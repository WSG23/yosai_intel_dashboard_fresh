package rbac

import (
	"context"
	"os"
	"strings"
	"sync"
	"time"
)

// RBACService retrieves and caches permissions for subjects.
type RBACService struct {
	mu    sync.Mutex
	ttl   time.Duration
	cache map[string]cacheEntry
}

type cacheEntry struct {
	perms []string
	exp   time.Time
}

// New returns a new RBACService with the given TTL for cached entries.
func New(ttl time.Duration) *RBACService {
	if ttl <= 0 {
		ttl = time.Minute
	}
	return &RBACService{ttl: ttl, cache: make(map[string]cacheEntry)}
}

// Permissions returns the permission list for a subject, populating the cache if needed.
func (r *RBACService) Permissions(ctx context.Context, subject string) ([]string, error) {
	r.mu.Lock()
	entry, ok := r.cache[subject]
	if ok && time.Now().Before(entry.exp) {
		perms := append([]string(nil), entry.perms...)
		r.mu.Unlock()
		return perms, nil
	}
	r.mu.Unlock()

	perms, err := r.fetchPermissions(ctx, subject)
	if err != nil {
		return nil, err
	}

	r.mu.Lock()
	r.cache[subject] = cacheEntry{perms: perms, exp: time.Now().Add(r.ttl)}
	r.mu.Unlock()
	return perms, nil
}

func (r *RBACService) fetchPermissions(ctx context.Context, subject string) ([]string, error) {
	// For this example permissions are provided via environment variables
	// using the key PERMISSIONS_<SUBJECT>. A fallback PERMISSIONS key is used
	// when none are defined for the specific subject.
	key := "PERMISSIONS_" + strings.ToUpper(subject)
	v := os.Getenv(key)
	if v == "" {
		v = os.Getenv("PERMISSIONS")
	}
	if v == "" {
		return nil, nil
	}
	parts := strings.Split(v, ",")
	perms := make([]string, 0, len(parts))
	for _, p := range parts {
		p = strings.TrimSpace(p)
		if p != "" {
			perms = append(perms, p)
		}
	}
	return perms, nil
}

// HasPermission checks if subject has the given permission.
func (r *RBACService) HasPermission(ctx context.Context, subject, perm string) (bool, error) {
	perms, err := r.Permissions(ctx, subject)
	if err != nil {
		return false, err
	}
	for _, p := range perms {
		if p == perm {
			return true, nil
		}
	}
	return false, nil
}
