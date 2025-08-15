package rbac

import (
	"context"
	"sync"
	"testing"
	"time"
)

type staticStore struct{ perms []string }

func (s staticStore) Permissions(ctx context.Context, subject string) ([]string, error) {
	return append([]string(nil), s.perms...), nil
}

// rbacServiceRW mirrors RBACService but uses an RWMutex for benchmarks.
type rbacServiceRW struct {
	mu    sync.RWMutex
	ttl   time.Duration
	cache map[string]cacheEntry
	store PermissionStore
}

func newRBACServiceRW(store PermissionStore, ttl time.Duration) *rbacServiceRW {
	if ttl <= 0 {
		ttl = time.Minute
	}
	return &rbacServiceRW{ttl: ttl, cache: make(map[string]cacheEntry), store: store}
}

func (r *rbacServiceRW) Permissions(ctx context.Context, subject string) ([]string, error) {
	r.mu.RLock()
	entry, ok := r.cache[subject]
	if ok && time.Now().Before(entry.exp) {
		perms := append([]string(nil), entry.perms...)
		r.mu.RUnlock()
		return perms, nil
	}
	r.mu.RUnlock()

	var perms []string
	var err error
	if r.store != nil {
		perms, err = r.store.Permissions(ctx, subject)
		if err != nil {
			return nil, err
		}
	}

	r.mu.Lock()
	r.cache[subject] = cacheEntry{perms: perms, exp: time.Now().Add(r.ttl)}
	r.mu.Unlock()
	return perms, nil
}

func (r *rbacServiceRW) HasPermission(ctx context.Context, subject, perm string) (bool, error) {
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

// TestRBACServiceConcurrentAccess ensures no races when multiple goroutines
// read permissions while the cache is concurrently invalidated.
func TestRBACServiceConcurrentAccess(t *testing.T) {
	svc := NewWithStore(staticStore{perms: []string{"read"}}, time.Minute)
	subject := "alice"
	ctx := context.Background()
	if _, err := svc.HasPermission(ctx, subject, "read"); err != nil {
		t.Fatalf("warmup failed: %v", err)
	}

	const goroutines = 1000
	start := make(chan struct{})
	var wg sync.WaitGroup
	for i := 0; i < goroutines/2; i++ {
		wg.Add(2)
		go func() {
			defer wg.Done()
			<-start
			if _, err := svc.HasPermission(ctx, subject, "read"); err != nil {
				t.Errorf("HasPermission failed: %v", err)
			}
		}()
		go func() {
			defer wg.Done()
			<-start
			svc.mu.Lock()
			delete(svc.cache, subject)
			svc.mu.Unlock()
		}()
	}
	close(start)
	wg.Wait()
}

// Benchmark read/write mixture for Mutex-based service.
func BenchmarkRBACServiceMutex(b *testing.B) {
	svc := NewWithStore(staticStore{perms: []string{"read"}}, time.Minute)
	ctx := context.Background()
	subject := "alice"
	b.ResetTimer()
	b.RunParallel(func(pb *testing.PB) {
		for pb.Next() {
			svc.HasPermission(ctx, subject, "read")
			svc.mu.Lock()
			delete(svc.cache, subject)
			svc.mu.Unlock()
		}
	})
}

// Benchmark read/write mixture for RWMutex-based service.
func BenchmarkRBACServiceRWMutex(b *testing.B) {
	svc := newRBACServiceRW(staticStore{perms: []string{"read"}}, time.Minute)
	ctx := context.Background()
	subject := "alice"
	b.ResetTimer()
	b.RunParallel(func(pb *testing.PB) {
		for pb.Next() {
			svc.HasPermission(ctx, subject, "read")
			svc.mu.Lock()
			delete(svc.cache, subject)
			svc.mu.Unlock()
		}
	})
}
