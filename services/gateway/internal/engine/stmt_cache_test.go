package engine

import (
	"context"
	"testing"

	"github.com/DATA-DOG/go-sqlmock"
)

func TestStmtCacheLRU(t *testing.T) {
	db, mock, err := sqlmock.New()
	if err != nil {
		t.Fatalf("sqlmock: %v", err)
	}
	defer db.Close()

	cache, err := NewStmtCache(db, 2)
	if err != nil {
		t.Fatalf("NewStmtCache: %v", err)
	}

	ctx := context.Background()

	mock.ExpectPrepare("SELECT 1")
	if _, err := cache.Get(ctx, "SELECT 1"); err != nil {
		t.Fatalf("first query: %v", err)
	}

	mock.ExpectPrepare("SELECT 2")
	if _, err := cache.Get(ctx, "SELECT 2"); err != nil {
		t.Fatalf("second query: %v", err)
	}

	if _, err := cache.Get(ctx, "SELECT 1"); err != nil {
		t.Fatalf("hit query: %v", err)
	}

	mock.ExpectPrepare("SELECT 3")
	if _, err := cache.Get(ctx, "SELECT 3"); err != nil {
		t.Fatalf("third query: %v", err)
	}

	mock.ExpectPrepare("SELECT 2")
	if _, err := cache.Get(ctx, "SELECT 2"); err != nil {
		t.Fatalf("evicted query: %v", err)
	}

	if cache.Hits() != 1 {
		t.Errorf("expected 1 hit, got %d", cache.Hits())
	}
	if cache.Misses() != 4 {
		t.Errorf("expected 4 misses, got %d", cache.Misses())
	}

	if err := mock.ExpectationsWereMet(); err != nil {
		t.Fatalf("unmet expectations: %v", err)
	}
}
