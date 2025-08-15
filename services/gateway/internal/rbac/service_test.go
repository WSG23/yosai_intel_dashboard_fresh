package rbac

import (
	"context"
	"sync"
	"testing"
	"time"

	"github.com/alicebob/miniredis/v2"
	"github.com/redis/go-redis/v9"
)

func TestRBACServiceCaching(t *testing.T) {
	t.Setenv("PERMISSIONS_ALICE", "read,write")
	svc := New(100 * time.Millisecond)

	perms, err := svc.Permissions(context.Background(), "alice")
	if err != nil {
		t.Fatal(err)
	}
	if len(perms) != 2 || perms[0] != "read" || perms[1] != "write" {
		t.Fatalf("unexpected perms: %v", perms)
	}

	t.Setenv("PERMISSIONS_ALICE", "read")
	perms, err = svc.Permissions(context.Background(), "alice")
	if err != nil {
		t.Fatal(err)
	}
	if len(perms) != 2 {
		t.Errorf("expected cached perms, got %v", perms)
	}

	time.Sleep(120 * time.Millisecond)
	perms, err = svc.Permissions(context.Background(), "alice")
	if err != nil {
		t.Fatal(err)
	}
	if len(perms) != 1 || perms[0] != "read" {
		t.Fatalf("expected refreshed perms, got %v", perms)
	}
}

func TestRBACServiceHasPermission(t *testing.T) {
	t.Setenv("PERMISSIONS_BOB", "alpha")
	svc := New(time.Minute)
	ok, err := svc.HasPermission(context.Background(), "bob", "alpha")
	if err != nil {
		t.Fatal(err)
	}
	if !ok {
		t.Fatal("expected true")
	}
	ok, err = svc.HasPermission(context.Background(), "bob", "beta")
	if err != nil {
		t.Fatal(err)
	}
	if ok {
		t.Fatal("expected false")
	}
}

func TestRBACServiceRedisStore(t *testing.T) {
	srv, err := miniredis.Run()
	if err != nil {
		t.Fatalf("failed to start miniredis: %v", err)
	}
	defer srv.Close()

	client := redis.NewClient(&redis.Options{Addr: srv.Addr()})
	if err := client.Set(context.Background(), "permissions:carol", "alpha,beta", 0).Err(); err != nil {
		t.Fatalf("failed to set redis key: %v", err)
	}

	svc := NewWithStore(NewRedisStore(client, "permissions"), time.Minute)
	perms, err := svc.Permissions(context.Background(), "carol")
	if err != nil {
		t.Fatal(err)
	}
	if len(perms) != 2 || perms[0] != "alpha" || perms[1] != "beta" {
		t.Fatalf("unexpected perms: %v", perms)
	}
}

func TestRBACServiceConcurrentAccess(t *testing.T) {
	t.Setenv("PERMISSIONS_DAVE", "read")
	svc := New(time.Millisecond)
	ctx := context.Background()

	var wg sync.WaitGroup
	const goroutines = 1000
	for i := 0; i < goroutines; i++ {
		wg.Add(1)
		go func(i int) {
			defer wg.Done()
			if i%2 == 0 {
				if _, err := svc.Permissions(ctx, "dave"); err != nil {
					t.Error(err)
				}
			} else {
				svc.mu.Lock()
				delete(svc.cache, "dave")
				svc.mu.Unlock()
			}
		}(i)
	}
	wg.Wait()
}

func BenchmarkRBACServiceMap(b *testing.B) {
	svc := New(time.Minute)
	ctx := context.Background()
	svc.cache["bob"] = cacheEntry{perms: []string{"alpha"}, exp: time.Now().Add(time.Hour)}

	b.RunParallel(func(pb *testing.PB) {
		for pb.Next() {
			if _, err := svc.Permissions(ctx, "bob"); err != nil {
				b.Fatalf("Permissions: %v", err)
			}
		}
	})
}

type syncMapService struct {
	ttl   time.Duration
	cache sync.Map
	store PermissionStore
}

func newSyncMapService(ttl time.Duration) *syncMapService {
	return &syncMapService{ttl: ttl}
}

func (r *syncMapService) Permissions(ctx context.Context, subject string) ([]string, error) {
	if v, ok := r.cache.Load(subject); ok {
		entry := v.(cacheEntry)
		if time.Now().Before(entry.exp) {
			return append([]string(nil), entry.perms...), nil
		}
	}

	perms, err := r.fetchPermissions(ctx, subject)
	if err != nil {
		return nil, err
	}
	r.cache.Store(subject, cacheEntry{perms: perms, exp: time.Now().Add(r.ttl)})
	return perms, nil
}

func (r *syncMapService) fetchPermissions(ctx context.Context, subject string) ([]string, error) {
	if r.store == nil {
		return nil, nil
	}
	return r.store.Permissions(ctx, subject)
}

func BenchmarkRBACServiceSyncMap(b *testing.B) {
	svc := newSyncMapService(time.Minute)
	ctx := context.Background()
	svc.cache.Store("bob", cacheEntry{perms: []string{"alpha"}, exp: time.Now().Add(time.Hour)})

	b.RunParallel(func(pb *testing.PB) {
		for pb.Next() {
			if _, err := svc.Permissions(ctx, "bob"); err != nil {
				b.Fatalf("Permissions: %v", err)
			}
		}
	})
}
