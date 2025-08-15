package cache

import "context"

// Decision represents an access control decision for a person at a door.
type Decision struct {
	PersonID string `json:"person"`
	DoorID   string `json:"door"`
	Decision string `json:"decision"`
}

// CacheService defines the interface for storing and retrieving decisions.
type CacheService interface {
	// GetDecision returns the cached decision for the person and door.
	// If no entry is found, (*Decision, nil) will be (nil, nil).
	GetDecision(ctx context.Context, personID, doorID string) (*Decision, error)

	// SetDecision stores a decision in the cache using the configured TTL.
	SetDecision(ctx context.Context, d Decision) error

	// InvalidateDecision removes the cached decision for the given person and door.
	InvalidateDecision(ctx context.Context, personID, doorID string) error
}
