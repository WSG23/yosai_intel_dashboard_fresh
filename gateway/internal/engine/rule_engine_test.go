package engine

import (
	"context"
	"fmt"
	"os"
	"sync"
	"testing"

	"github.com/DATA-DOG/go-sqlmock"
	"github.com/alicebob/miniredis/v2"
	"github.com/sony/gobreaker"

	"github.com/WSG23/yosai-gateway/internal/cache"
)

func TestRuleEngineEvaluateAccess(t *testing.T) {
	db, mock, err := sqlmock.New()
	if err != nil {
		t.Fatalf("sqlmock: %v", err)
	}
	defer db.Close()

	mock.ExpectPrepare(queryEvaluate)
	mock.ExpectPrepare(queryWarm)

	eng, err := NewRuleEngineWithSettings(db, gobreaker.Settings{}, 2)
	if err != nil {
		t.Fatalf("NewRuleEngineWithSettings: %v", err)
	}

	rows := sqlmock.NewRows([]string{"person_id", "door_id", "decision"}).AddRow("p", "d", "Granted")
	mock.ExpectQuery(queryEvaluate).WithArgs("p", "d").WillReturnRows(rows)

	dec, err := eng.EvaluateAccess(context.Background(), "p", "d")
	if err != nil {
		t.Fatalf("EvaluateAccess: %v", err)
	}
	if dec.Decision != "Granted" {
		t.Fatalf("unexpected decision: %s", dec.Decision)
	}

	if err := mock.ExpectationsWereMet(); err != nil {
		t.Fatalf("unmet expectations: %v", err)
	}
}

func setupRedis(t *testing.T) (*miniredis.Miniredis, cache.CacheService) {
	srv, err := miniredis.Run()
	if err != nil {
		t.Fatalf("miniredis: %v", err)
	}
	os.Setenv("REDIS_HOST", srv.Host())
	os.Setenv("REDIS_PORT", srv.Port())
	os.Setenv("CACHE_TTL_SECONDS", "60")
	return srv, cache.NewRedisCache()
}

func TestCachedRuleEngineUsesCache(t *testing.T) {
	srv, c := setupRedis(t)
	defer srv.Close()

	db, mock, err := sqlmock.New()
	if err != nil {
		t.Fatalf("sqlmock: %v", err)
	}
	defer db.Close()

	mock.ExpectPrepare(queryEvaluate)
	mock.ExpectPrepare(queryWarm)

	eng, err := NewRuleEngineWithSettings(db, gobreaker.Settings{}, 2)
	if err != nil {
		t.Fatalf("NewRuleEngineWithSettings: %v", err)
	}

	cre := &CachedRuleEngine{Engine: eng, Cache: c}
	rows := sqlmock.NewRows([]string{"person_id", "door_id", "decision"}).AddRow("p", "d", "Granted")
	mock.ExpectQuery(queryEvaluate).WithArgs("p", "d").WillReturnRows(rows)

	ctx := context.Background()
	if _, err := cre.EvaluateAccess(ctx, "p", "d"); err != nil {
		t.Fatalf("first evaluate: %v", err)
	}
	// second call should hit cache and not trigger DB query
	if _, err := cre.EvaluateAccess(ctx, "p", "d"); err != nil {
		t.Fatalf("second evaluate: %v", err)
	}

	if err := mock.ExpectationsWereMet(); err != nil {
		t.Fatalf("unmet expectations: %v", err)
	}
}

func TestCachedRuleEngineConcurrentAccess(t *testing.T) {
	srv, c := setupRedis(t)
	defer srv.Close()

	dec := cache.Decision{PersonID: "p", DoorID: "d", Decision: "Granted"}
	if err := c.SetDecision(context.Background(), dec); err != nil {
		t.Fatalf("seed cache: %v", err)
	}

	cre := &CachedRuleEngine{Engine: &RuleEngine{}, Cache: c}

	const n = 10
	var wg sync.WaitGroup
	wg.Add(n)
	errs := make(chan error, n)
	for i := 0; i < n; i++ {
		go func() {
			defer wg.Done()
			d, err := cre.EvaluateAccess(context.Background(), "p", "d")
			if err != nil {
				errs <- err
				return
			}
			if d.Decision != "Granted" {
				errs <- fmt.Errorf("got %s", d.Decision)
			}
		}()
	}
	wg.Wait()
	close(errs)
	for e := range errs {
		if e != nil {
			t.Fatalf("EvaluateAccess: %v", e)
		}
	}
}

func TestCachedRuleEngineInvalidation(t *testing.T) {
	srv, c := setupRedis(t)
	defer srv.Close()

	db, mock, err := sqlmock.New()
	if err != nil {
		t.Fatalf("sqlmock: %v", err)
	}
	defer db.Close()

	mock.ExpectPrepare(queryEvaluate)
	mock.ExpectPrepare(queryWarm)

	eng, err := NewRuleEngineWithSettings(db, gobreaker.Settings{}, 2)
	if err != nil {
		t.Fatalf("NewRuleEngineWithSettings: %v", err)
	}
	cre := &CachedRuleEngine{Engine: eng, Cache: c}
	ctx := context.Background()

	rows1 := sqlmock.NewRows([]string{"person_id", "door_id", "decision"}).AddRow("p", "d", "Granted")
	mock.ExpectQuery(queryEvaluate).WithArgs("p", "d").WillReturnRows(rows1)
	if d, err := cre.EvaluateAccess(ctx, "p", "d"); err != nil || d.Decision != "Granted" {
		t.Fatalf("first evaluate: %v, %+v", err, d)
	}
	if d, err := cre.EvaluateAccess(ctx, "p", "d"); err != nil || d.Decision != "Granted" {
		t.Fatalf("cached evaluate: %v, %+v", err, d)
	}

	if err := c.InvalidateDecision(ctx, "p", "d"); err != nil {
		t.Fatalf("invalidate: %v", err)
	}

	rows2 := sqlmock.NewRows([]string{"person_id", "door_id", "decision"}).AddRow("p", "d", "Denied")
	mock.ExpectQuery(queryEvaluate).WithArgs("p", "d").WillReturnRows(rows2)

	d, err := cre.EvaluateAccess(ctx, "p", "d")
	if err != nil {
		t.Fatalf("post-invalidate evaluate: %v", err)
	}
	if d.Decision != "Denied" {
		t.Fatalf("expected Denied, got %s", d.Decision)
	}

	if err := mock.ExpectationsWereMet(); err != nil {
		t.Fatalf("unmet expectations: %v", err)
	}
}
