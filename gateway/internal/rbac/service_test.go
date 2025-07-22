package rbac

import (
	"context"
	"testing"
	"time"
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
