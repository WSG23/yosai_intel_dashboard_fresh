package events

import (
	"context"
	"time"

	"github.com/WSG23/yosai-gateway/internal/cache"
)

// CachedRuleEngine evaluates access events while optionally caching decisions.
type CachedRuleEngine struct {
	cache cache.CacheService
}

// NewCachedRuleEngine returns a new CachedRuleEngine instance.
func NewCachedRuleEngine(c cache.CacheService) *CachedRuleEngine {
	return &CachedRuleEngine{cache: c}
}

// Evaluate computes the access decision for e and caches the result if a cache
// service is configured. In this simplified example the event's existing
// AccessResult value is used when no cached entry exists.
func (cr *CachedRuleEngine) Evaluate(ctx context.Context, e *AccessEvent) error {
	if cr.cache != nil {
		if d, err := cr.cache.GetDecision(ctx, e.PersonID, e.DoorID); err == nil && d != nil {
			e.AccessResult = d.Decision
			e.ProcessedAt = time.Now()
			return nil
		}
	}

	if err := e.Validate(); err != nil {
		return err
	}

	if e.AccessResult == "" {
		e.AccessResult = "allow"
	}
	e.ProcessedAt = time.Now()

	if cr.cache != nil {
		_ = cr.cache.SetDecision(ctx, cache.Decision{
			PersonID: e.PersonID,
			DoorID:   e.DoorID,
			Decision: e.AccessResult,
		})
	}
	return nil
}
