package rbac_test

import (
    "context"
    "errors"
    "os"
    "testing"

    sqlmock "github.com/DATA-DOG/go-sqlmock"
    "github.com/alicebob/miniredis/v2"
    "github.com/redis/go-redis/v9"

    rbac "github.com/WSG23/yosai-gateway/internal/rbac"
)

func TestEnvStore(t *testing.T) {
    os.Setenv("PERMISSIONS_ALICE", "read, write ,")
    defer os.Unsetenv("PERMISSIONS_ALICE")
    perms, err := (rbac.EnvStore{}).Permissions(context.Background(), "alice")
    if err != nil {
        t.Fatalf("unexpected error: %v", err)
    }
    if len(perms) != 2 || perms[0] != "read" || perms[1] != "write" {
        t.Fatalf("unexpected perms: %v", perms)
    }
}

func TestRedisStore(t *testing.T) {
    srv := miniredis.RunT(t)
    client := redis.NewClient(&redis.Options{Addr: srv.Addr()})
    if err := client.Set(context.Background(), "permissions:alice", "read", 0).Err(); err != nil {
        t.Fatalf("set: %v", err)
    }
    store := rbac.NewRedisStore(client, "")
    perms, err := store.Permissions(context.Background(), "Alice")
    if err != nil || len(perms) != 1 || perms[0] != "read" {
        t.Fatalf("unexpected perms %v err %v", perms, err)
    }
}

func TestRedisStoreError(t *testing.T) {
    client := redis.NewClient(&redis.Options{Addr: "bad:1234"})
    store := rbac.NewRedisStore(client, "p")
    if _, err := store.Permissions(context.Background(), "u"); err == nil {
        t.Fatal("expected error")
    }
}

func TestSQLStore(t *testing.T) {
    db, mock, err := sqlmock.New()
    if err != nil {
        t.Fatalf("sqlmock: %v", err)
    }
    defer db.Close()
    rows := sqlmock.NewRows([]string{"name"}).AddRow("read").AddRow("write")
    mock.ExpectQuery("SELECT p.name").WithArgs("u").WillReturnRows(rows)
    store := rbac.NewSQLStore(db)
    perms, err := store.Permissions(context.Background(), "u")
    if err != nil || len(perms) != 2 {
        t.Fatalf("unexpected %v err %v", perms, err)
    }
}

func TestSQLStoreQueryError(t *testing.T) {
    db, mock, err := sqlmock.New()
    if err != nil {
        t.Fatalf("sqlmock: %v", err)
    }
    defer db.Close()
    mock.ExpectQuery("SELECT p.name").WithArgs("u").WillReturnError(errors.New("boom"))
    store := rbac.NewSQLStore(db)
    if _, err := store.Permissions(context.Background(), "u"); err == nil {
        t.Fatal("expected error")
    }
}

