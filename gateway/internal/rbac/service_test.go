package rbac

import (
	"context"
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
