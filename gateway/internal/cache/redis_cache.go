package cache

import (
	"context"
	"encoding/json"
	"errors"
	"fmt"
	"math/rand"
	"os"
	"strconv"
	"time"

	"github.com/prometheus/client_golang/prometheus"
	"github.com/redis/go-redis/v9"
	"github.com/sony/gobreaker"

	"github.com/WSG23/resilience"
	"go.opentelemetry.io/otel"
)

var (
	cacheHits = prometheus.NewCounter(prometheus.CounterOpts{
		Name: "gateway_cache_hits_total",
		Help: "Number of cache hits",
	})
	cacheMisses = prometheus.NewCounter(prometheus.CounterOpts{
		Name: "gateway_cache_misses_total",
		Help: "Number of cache misses",
	})
)

func init() {
	prometheus.MustRegister(cacheHits, cacheMisses)
}

// RedisCache implements CacheService backed by Redis.
type RedisCache struct {
	client  *redis.Client
	ttl     time.Duration
	breaker *gobreaker.CircuitBreaker
}

// NewRedisCache creates a Redis-backed cache service configured via environment variables.
func NewRedisCache() *RedisCache {
	host := os.Getenv("REDIS_HOST")
	if host == "" {
		host = "localhost"
	}
	port := os.Getenv("REDIS_PORT")
	if port == "" {
		port = "6379"
	}
	ttl := 300
	if v := os.Getenv("CACHE_TTL_SECONDS"); v != "" {
		if n, err := strconv.Atoi(v); err == nil && n > 0 {
			ttl = n
		}
	}
	client := redis.NewClient(&redis.Options{Addr: fmt.Sprintf("%s:%s", host, port)})
	settings := gobreaker.Settings{
		Name:        "redis-cache",
		ReadyToTrip: func(c gobreaker.Counts) bool { return c.ConsecutiveFailures >= 3 },
		Timeout:     100*time.Millisecond + time.Duration(rand.Intn(100))*time.Millisecond,
	}
	cb := resilience.NewGoBreaker("redis-cache", settings)
	return &RedisCache{client: client, ttl: time.Duration(ttl) * time.Second, breaker: cb}
}

func (r *RedisCache) key(person, door string) string {
        return fmt.Sprintf("decision:%s:%s", person, door)
}

// GetDecision retrieves a decision from Redis. Missing keys and timeouts return nil with no error.
func (r *RedisCache) GetDecision(ctx context.Context, personID, doorID string) (*Decision, error) {
	ctx, span := otel.Tracer("redis").Start(ctx, "GetDecision")
	defer span.End()
	ctx, cancel := context.WithTimeout(ctx, 20*time.Millisecond)
	defer cancel()
       var val string
       _, err := r.breaker.Execute(func() (interface{}, error) {
               v, e := r.client.Get(ctx, r.key(personID, doorID)).Result()
               if e != nil {
                       if errors.Is(e, redis.Nil) {
                               return nil, nil
                       }
                       return nil, e
               }
               val = v
               return nil, nil
       })
       if err != nil || val == "" {
               cacheMisses.Inc()
               return nil, err
       }
       cacheHits.Inc()
       var d Decision
       if err := json.Unmarshal([]byte(val), &d); err != nil {
               return nil, err
       }
       return &d, nil
}

// SetDecision stores a decision in Redis using the configured TTL. Timeouts are ignored.
func (r *RedisCache) SetDecision(ctx context.Context, d Decision) error {
	ctx, span := otel.Tracer("redis").Start(ctx, "SetDecision")
	defer span.End()
	data, err := json.Marshal(d)
	if err != nil {
		span.RecordError(err)
		return err
	}
	ctx, cancel := context.WithTimeout(ctx, 20*time.Millisecond)
	defer cancel()
	_, err = r.breaker.Execute(func() (interface{}, error) {
		return nil, r.client.Set(ctx, r.key(d.PersonID, d.DoorID), data, r.ttl).Err()
	})
	if err != nil {
		span.RecordError(err)
	}
	return err
}

// InvalidateDecision removes a cached decision for the given person and door.
func (r *RedisCache) InvalidateDecision(ctx context.Context, personID, doorID string) error {
	ctx, span := otel.Tracer("redis").Start(ctx, "InvalidateDecision")
	defer span.End()
	ctx, cancel := context.WithTimeout(ctx, 20*time.Millisecond)
	defer cancel()
	_, err := r.breaker.Execute(func() (interface{}, error) {
		return nil, r.client.Del(ctx, r.key(personID, doorID)).Err()
	})
	if err != nil {
		span.RecordError(err)
	}
	return err
}
