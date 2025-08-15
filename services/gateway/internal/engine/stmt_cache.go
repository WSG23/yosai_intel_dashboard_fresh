package engine

import (
	"context"
	"database/sql"
	"sync"

	lru "github.com/hashicorp/golang-lru"

	"github.com/WSG23/yosai-gateway/internal/tracing"
)

// StmtCache caches prepared statements with LRU eviction.
type StmtCache struct {
	db   *sql.DB
	mu   sync.Mutex
	lru  *lru.Cache
	hits uint64
	miss uint64
}

// NewStmtCache creates a new prepared statement cache with the given size.
func NewStmtCache(db *sql.DB, size int) (*StmtCache, error) {
	cache, err := lru.NewWithEvict(size, func(key, value interface{}) {
		if stmt, ok := value.(*sql.Stmt); ok {
			_ = stmt.Close()
		}
		tracing.Logger.WithField("query", key).Debug("evicted prepared statement")
	})
	if err != nil {
		return nil, err
	}
	return &StmtCache{db: db, lru: cache}, nil
}

// Get returns a prepared statement for the query, preparing and caching it if necessary.
func (c *StmtCache) Get(ctx context.Context, query string) (*sql.Stmt, error) {
	c.mu.Lock()
	defer c.mu.Unlock()

	if stmt, ok := c.lru.Get(query); ok {
		c.hits++
		tracing.Logger.WithContext(ctx).WithField("query", query).Debug("prepared statement cache hit")
		return stmt.(*sql.Stmt), nil
	}

	c.miss++
	tracing.Logger.WithContext(ctx).WithField("query", query).Debug("prepared statement cache miss")
	stmt, err := c.db.PrepareContext(ctx, query)
	if err != nil {
		return nil, err
	}
	c.lru.Add(query, stmt)
	return stmt, nil
}

// Hits returns the number of cache hits.
func (c *StmtCache) Hits() uint64 {
	c.mu.Lock()
	defer c.mu.Unlock()
	return c.hits
}

// Misses returns the number of cache misses.
func (c *StmtCache) Misses() uint64 {
	c.mu.Lock()
	defer c.mu.Unlock()
	return c.miss
}
