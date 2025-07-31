package repository

import (
	"context"
	"sync"
)

// TokenStore records processed event tokens for idempotency.
type TokenStore interface {
	IsProcessed(ctx context.Context, token string) (bool, error)
	MarkProcessed(ctx context.Context, token string) error
	Rollback(ctx context.Context, token string) error
}

// MemoryTokenStore is an in-memory TokenStore implementation.
type MemoryTokenStore struct {
	mu     sync.Mutex
	tokens map[string]struct{}
}

func NewMemoryTokenStore() *MemoryTokenStore {
	return &MemoryTokenStore{tokens: make(map[string]struct{})}
}

func (m *MemoryTokenStore) IsProcessed(ctx context.Context, token string) (bool, error) {
	m.mu.Lock()
	defer m.mu.Unlock()
	_, ok := m.tokens[token]
	return ok, nil
}

func (m *MemoryTokenStore) MarkProcessed(ctx context.Context, token string) error {
	m.mu.Lock()
	defer m.mu.Unlock()
	m.tokens[token] = struct{}{}
	return nil
}

func (m *MemoryTokenStore) Rollback(ctx context.Context, token string) error {
	m.mu.Lock()
	defer m.mu.Unlock()
	delete(m.tokens, token)
	return nil
}
