package rbac

import (
	"context"
	"sync"
	"time"
)

// RBACService retrieves and caches permissions for subjects.
type RBACService struct {
	mu    sync.RWMutex
	ttl   time.Duration
	cache map[string]cacheEntry
	store PermissionStore
}

type cacheEntry struct {
	perms []string
	exp   time.Time
}

// New returns a new RBACService with the given TTL for cached entries.
func New(ttl time.Duration) *RBACService {
	return NewWithStore(EnvStore{}, ttl)
}

// NewWithStore returns a new RBACService with the provided store and TTL for cached entries.
func NewWithStore(store PermissionStore, ttl time.Duration) *RBACService {
	if ttl <= 0 {
		ttl = time.Minute
	}
	return &RBACService{ttl: ttl, cache: make(map[string]cacheEntry), store: store}
}

// Permissions returns the permission list for a subject, populating the cache if needed.
func (r *RBACService) Permissions(ctx context.Context, subject string) ([]string, error) {
	r.mu.RLock()
	entry, ok := r.cache[subject]
	if ok && time.Now().Before(entry.exp) {
		perms := append([]string(nil), entry.perms...)
		r.mu.RUnlock()
		return perms, nil
	}
	r.mu.RUnlock()

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
	if r.store == nil {
		return nil, nil
	}
	return r.store.Permissions(ctx, subject)
}

// HasPermission checks if subject has the given permission.
func (r *RBACService) HasPermission(ctx context.Context, subject, perm string) (bool, error) {
	r.mu.RLock()
	entry, ok := r.cache[subject]
	if ok && time.Now().Before(entry.exp) {
		perms := append([]string(nil), entry.perms...)
		r.mu.RUnlock()
		for _, p := range perms {
			if p == perm {
				return true, nil
			}
		}
		return false, nil
	}
	r.mu.RUnlock()

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
