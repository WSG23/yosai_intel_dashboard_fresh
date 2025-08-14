package cache

import (
	"bytes"
	"context"
	"crypto/sha256"
	"encoding/hex"
	"encoding/json"
	"fmt"
	"io"
	"net/http"
	"net/http/httptest"
	"time"

	"github.com/prometheus/client_golang/prometheus"
	"github.com/redis/go-redis/v9"
	"github.com/sony/gobreaker"

	"github.com/WSG23/yosai-gateway/internal/tracing"
)

// CacheRule defines caching behaviour for a specific path.
type CacheRule struct {
	Path            string        // path to cache
	TTL             time.Duration // TTL for cached entries
	VaryHeaders     []string      // request headers that affect the cache key
	VaryParams      []string      // query params that affect the cache key
	InvalidatePaths []string      // paths that when requested invalidate this cache
}

// cachedResponse represents the stored response payload.
type cachedResponse struct {
	StatusCode int
	Headers    http.Header
	Body       []byte
}

// CachePlugin is an HTTP middleware caching GET/HEAD responses in Redis.
type CachePlugin struct {
	redis   *redis.Client
	rules   []CacheRule
	breaker *gobreaker.CircuitBreaker
}

// NewCachePlugin creates a CachePlugin using the provided Redis client and rules.
func NewCachePlugin(client *redis.Client, rules []CacheRule) *CachePlugin {
	settings := gobreaker.Settings{
		Name:    "analytics-service",
		Timeout: 30 * time.Second,
		ReadyToTrip: func(c gobreaker.Counts) bool {
			return c.ConsecutiveFailures >= 3
		},
	}
	return &CachePlugin{redis: client, rules: rules, breaker: gobreaker.NewCircuitBreaker(settings)}
}

var (
	apiCacheHits = prometheus.NewCounter(prometheus.CounterOpts{
		Name: "gateway_api_cache_hits_total",
		Help: "Number of API cache hits",
	})
	apiCacheMisses = prometheus.NewCounter(prometheus.CounterOpts{
		Name: "gateway_api_cache_misses_total",
		Help: "Number of API cache misses",
	})
	analyticsFallbacks = prometheus.NewCounter(prometheus.CounterOpts{
		Name: "gateway_analytics_fallback_total",
		Help: "Number of analytics requests served from cache or default due to service errors",
	})
)

func init() {
	prometheus.MustRegister(apiCacheHits, apiCacheMisses, analyticsFallbacks)
}

func (c *CachePlugin) Name() string                        { return "api-cache" }
func (c *CachePlugin) Priority() int                       { return 50 }
func (c *CachePlugin) Init(_ map[string]interface{}) error { return nil }

// invalidate removes cached entries for the given rule.
func (c *CachePlugin) invalidate(ctx context.Context, rule CacheRule) {
	pattern := "cache:" + rule.Path + ":*"
	iter := c.redis.Scan(ctx, 0, pattern, 0).Iterator()
	for iter.Next(ctx) {
		c.redis.Del(ctx, iter.Val())
	}
}

// Process implements the middleware logic.
func (c *CachePlugin) Process(ctx context.Context, req *http.Request, resp http.ResponseWriter, next http.Handler) {
	for _, r := range c.rules {
		// Invalidate cache if this request matches an invalidation path
		for _, p := range r.InvalidatePaths {
			if p == req.URL.Path {
				c.invalidate(ctx, r)
			}
		}

		// Handle caching for matching path and GET/HEAD methods
		if r.Path == req.URL.Path && (req.Method == http.MethodGet || req.Method == http.MethodHead) {
			key := cacheKey(req, r)
			val, err := c.redis.Get(ctx, key).Result()
			if err == nil {
				var cr cachedResponse
				if json.Unmarshal([]byte(val), &cr) == nil {
					for k, v := range cr.Headers {
						resp.Header()[k] = v
					}
					resp.Header().Set("X-Cache", "HIT")
					apiCacheHits.Inc()
					resp.WriteHeader(cr.StatusCode)
					if req.Method != http.MethodHead {
						resp.Write(cr.Body)
					}
					return
				}
			}

			apiCacheMisses.Inc()
			recorder := httptest.NewRecorder()
			_, execErr := c.breaker.Execute(func() (interface{}, error) {
				next.ServeHTTP(recorder, req)
				if recorder.Result().StatusCode >= http.StatusInternalServerError {
					return nil, fmt.Errorf("status %d", recorder.Result().StatusCode)
				}
				return nil, nil
			})
			res := recorder.Result()
			body, _ := io.ReadAll(res.Body)
			res.Body.Close()

			if execErr != nil {
				tracing.Logger.WithError(execErr).Error("analytics service request failed")
				analyticsFallbacks.Inc()
				// attempt to serve stale cache again (if any)
				if err == nil {
					var cr cachedResponse
					if json.Unmarshal([]byte(val), &cr) == nil {
						for k, v := range cr.Headers {
							resp.Header()[k] = v
						}
						resp.Header().Set("X-Cache", "STALE")
						resp.WriteHeader(cr.StatusCode)
						if req.Method != http.MethodHead {
							resp.Write(cr.Body)
						}
						return
					}
				}
				resp.Header().Set("Content-Type", "application/json")
				resp.Header().Set("X-Cache", "EMPTY")
				resp.WriteHeader(http.StatusOK)
				if req.Method != http.MethodHead {
					resp.Write([]byte("{}"))
				}
				return
			}

			if res.StatusCode < 300 {
				data, _ := json.Marshal(cachedResponse{StatusCode: res.StatusCode, Headers: res.Header, Body: body})
				c.redis.Set(ctx, key, data, r.TTL)
			}

			for k, v := range res.Header {
				resp.Header()[k] = v
			}
			resp.Header().Set("X-Cache", "MISS")
			resp.WriteHeader(res.StatusCode)
			if req.Method != http.MethodHead {
				resp.Write(body)
			}
			return
		}
	}

	// No rule matched, just pass through
	next.ServeHTTP(resp, req)
}

// cacheKey builds a cache key for the request respecting vary options.
func cacheKey(req *http.Request, rule CacheRule) string {
	var b bytes.Buffer
	b.WriteString(req.Method)
	for _, h := range rule.VaryHeaders {
		b.WriteString("|")
		b.WriteString(req.Header.Get(h))
	}
	q := req.URL.Query()
	for _, p := range rule.VaryParams {
		b.WriteString("|")
		b.WriteString(q.Get(p))
	}
	sum := sha256.Sum256(b.Bytes())
	return "cache:" + rule.Path + ":" + hex.EncodeToString(sum[:])
}
