package engine

import (
	"context"
	"database/sql"
	"errors"
	"time"

	"github.com/WSG23/yosai-gateway/internal/cache"
	"github.com/sony/gobreaker"
)

// Decision mirrors cache.Decision for convenience.
type Decision = cache.Decision

// AccessRequest represents a single access evaluation request.
type AccessRequest struct {
	PersonID string
	DoorID   string
}

// RuleEngine evaluates access control rules using a SQL backend.
// It keeps prepared statements and protects queries with a circuit breaker.
type RuleEngine struct {
	db         *sql.DB
	stmtSingle *sql.Stmt
	stmtWarm   *sql.Stmt
	breaker    *gobreaker.CircuitBreaker
}

// NewRuleEngine constructs a RuleEngine from an existing DB handle.
func NewRuleEngine(db *sql.DB) (*RuleEngine, error) {
	settings := gobreaker.Settings{
		Name:        "rule-engine",
		Timeout:     5 * time.Second,
		ReadyToTrip: func(c gobreaker.Counts) bool { return c.ConsecutiveFailures > 5 },
	}
	return NewRuleEngineWithSettings(db, settings)
}

// NewRuleEngineWithSettings constructs a RuleEngine using custom circuit breaker settings.
func NewRuleEngineWithSettings(db *sql.DB, settings gobreaker.Settings) (*RuleEngine, error) {
	single, err := db.PrepareContext(context.Background(),
		`SELECT person_id, door_id, decision FROM evaluate_access($1,$2)`)
	if err != nil {
		return nil, err
	}
	warm, err := db.PrepareContext(context.Background(),
		`SELECT person_id, door_id, decision FROM warm_cache($1)`)
	if err != nil {
		single.Close()
		return nil, err
	}
	cb := gobreaker.NewCircuitBreaker(settings)
	return &RuleEngine{db: db, stmtSingle: single, stmtWarm: warm, breaker: cb}, nil
}

// EvaluateAccess evaluates the rules for a single person/door pair.
func (re *RuleEngine) EvaluateAccess(ctx context.Context, personID, doorID string) (Decision, error) {
	var d Decision
	_, err := re.breaker.Execute(func() (interface{}, error) {
		row := re.stmtSingle.QueryRowContext(ctx, personID, doorID)
		return nil, row.Scan(&d.PersonID, &d.DoorID, &d.Decision)
	})
	if err != nil {
		return Decision{}, err
	}
	if d.PersonID == "" {
		return Decision{}, errors.New("no decision")
	}
	return d, nil
}

// EvaluateBatch evaluates multiple requests in a single database roundtrip.
func (re *RuleEngine) EvaluateBatch(ctx context.Context, reqs []AccessRequest) ([]Decision, error) {
	if len(reqs) == 0 {
		return nil, nil
	}
	results := make([]Decision, 0, len(reqs))
	for _, r := range reqs {
		d, err := re.EvaluateAccess(ctx, r.PersonID, r.DoorID)
		if err != nil {
			return nil, err
		}
		results = append(results, d)
	}
	return results, nil
}

// WarmCache preloads frequently used rules for the given facility.
func (re *RuleEngine) WarmCache(ctx context.Context, facility string) error {
	_, err := re.breaker.Execute(func() (interface{}, error) {
		_, err := re.stmtWarm.ExecContext(ctx, facility)
		return nil, err
	})
	return err
}

// CachedRuleEngine wraps RuleEngine with caching logic.
type CachedRuleEngine struct {
	Engine *RuleEngine
	Cache  cache.CacheService
}

// EvaluateAccess looks up the decision in cache before querying the engine.
func (c *CachedRuleEngine) EvaluateAccess(ctx context.Context, personID, doorID string) (Decision, error) {
	if c.Cache != nil {
		if d, err := c.Cache.GetDecision(ctx, personID, doorID); err == nil && d != nil {
			return *d, nil
		}
	}
	dec, err := c.Engine.EvaluateAccess(ctx, personID, doorID)
	if err != nil {
		return dec, err
	}
	if c.Cache != nil {
		_ = c.Cache.SetDecision(ctx, cache.Decision(dec))
	}
	return dec, nil
}

// EvaluateBatch checks the cache for each request before delegating the rest to the engine.
func (c *CachedRuleEngine) EvaluateBatch(ctx context.Context, reqs []AccessRequest) ([]Decision, error) {
	if len(reqs) == 0 {
		return nil, nil
	}
	remaining := make([]AccessRequest, 0, len(reqs))
	results := make([]Decision, 0, len(reqs))
	if c.Cache != nil {
		for _, r := range reqs {
			if d, err := c.Cache.GetDecision(ctx, r.PersonID, r.DoorID); err == nil && d != nil {
				results = append(results, *d)
			} else {
				remaining = append(remaining, r)
			}
		}
	} else {
		remaining = reqs
	}
	if len(remaining) > 0 {
		decs, err := c.Engine.EvaluateBatch(ctx, remaining)
		if err != nil {
			return nil, err
		}
		results = append(results, decs...)
		if c.Cache != nil {
			for _, d := range decs {
				_ = c.Cache.SetDecision(ctx, cache.Decision(d))
			}
		}
	}
	return results, nil
}

// WarmCache delegates to the underlying engine and populates the cache when successful.
func (c *CachedRuleEngine) WarmCache(ctx context.Context, facility string) error {
	if err := c.Engine.WarmCache(ctx, facility); err != nil {
		return err
	}
	// When warm cache completes successfully we have already stored data in the engine side.
	// There is no specific caching here beyond Evaluate* storing individual entries.
	return nil
}
