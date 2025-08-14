package cache

import (
	"context"
	"encoding/json"
	"errors"
	"sync"
	"time"

	"github.com/bits-and-blooms/bloom/v3"
	"github.com/prometheus/client_golang/prometheus"
	"github.com/redis/go-redis/v9"

	"github.com/WSG23/yosai-gateway/internal/auth"
)

// TokenCache provides caching and blacklist operations for JWT tokens using Redis.
type TokenCache struct {
	client   *redis.Client
	blFilter *bloom.BloomFilter
	mu       sync.RWMutex
}

// NewTokenCache returns a new TokenCache using the given Redis client.
func NewTokenCache(client *redis.Client) *TokenCache {
	filter := bloom.NewWithEstimates(100000, 0.01)
	return &TokenCache{client: client, blFilter: filter}
}

func tokenKey(id string) string     { return "token:" + id }
func blacklistKey(id string) string { return "blacklist:" + id }

var (
	tokenCacheHits = prometheus.NewCounter(prometheus.CounterOpts{
		Name: "gateway_token_cache_hits_total",
		Help: "Number of token cache hits",
	})
	tokenCacheMisses = prometheus.NewCounter(prometheus.CounterOpts{
		Name: "gateway_token_cache_misses_total",
		Help: "Number of token cache misses",
	})
)

func init() {
	prometheus.MustRegister(tokenCacheHits, tokenCacheMisses)
}

// Get retrieves cached claims for a token ID. Missing keys and timeouts are not treated as errors.
func (t *TokenCache) Get(ctx context.Context, tokenID string) (*auth.EnhancedClaims, error) {
	ctx, cancel := context.WithTimeout(ctx, 500*time.Millisecond)
	defer cancel()

	val, err := t.client.Get(ctx, tokenKey(tokenID)).Result()
	if err != nil {
		if err == redis.Nil || errors.Is(err, context.DeadlineExceeded) {
			tokenCacheMisses.Inc()
			return nil, nil
		}
		return nil, err
	}
	tokenCacheHits.Inc()
	var claims auth.EnhancedClaims
	if err := json.Unmarshal([]byte(val), &claims); err != nil {
		return nil, err
	}
	return &claims, nil
}

// Set stores claims for a token ID with the provided TTL. Timeouts are ignored.
func (t *TokenCache) Set(ctx context.Context, tokenID string, claims *auth.EnhancedClaims, ttl time.Duration) error {
	data, err := json.Marshal(claims)
	if err != nil {
		return err
	}
	ctx, cancel := context.WithTimeout(ctx, 500*time.Millisecond)
	defer cancel()
	return t.client.Set(ctx, tokenKey(tokenID), data, ttl).Err()
}

// Delete removes cached claims for the given token ID.
func (t *TokenCache) Delete(ctx context.Context, tokenID string) error {
	ctx, cancel := context.WithTimeout(ctx, 500*time.Millisecond)
	defer cancel()
	return t.client.Del(ctx, tokenKey(tokenID)).Err()
}

// Blacklist marks a token ID as invalid for the given TTL.
func (t *TokenCache) Blacklist(ctx context.Context, tokenID string, ttl time.Duration) error {
	ctx, cancel := context.WithTimeout(ctx, 500*time.Millisecond)
	defer cancel()
	t.mu.Lock()
	t.blFilter.AddString(tokenID)
	t.mu.Unlock()
	return t.client.Set(ctx, blacklistKey(tokenID), "1", ttl).Err()
}

// IsBlacklisted checks whether the token ID is blacklisted. Missing keys and timeouts return false with no error.
func (t *TokenCache) IsBlacklisted(ctx context.Context, tokenID string) (bool, error) {
	ctx, cancel := context.WithTimeout(ctx, 500*time.Millisecond)
	defer cancel()

	t.mu.RLock()
	inFilter := t.blFilter.TestString(tokenID)
	t.mu.RUnlock()
	if !inFilter {
		return false, nil
	}
	exists, err := t.client.Exists(ctx, blacklistKey(tokenID)).Result()
	if err != nil {
		if err == redis.Nil || errors.Is(err, context.DeadlineExceeded) {
			return false, nil
		}
		return false, err
	}
	return exists == 1, nil
}
