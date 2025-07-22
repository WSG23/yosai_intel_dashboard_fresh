package ratelimit

import (
	"context"
	"fmt"
	"net/http"
	"os"
	"strconv"
	"time"

	"github.com/redis/go-redis/v9"
)

// SlidingWindowPlugin implements a Redis backed sliding window rate limiter.
// It enforces per-user and global request limits with optional delaying of
// requests that exceed the configured window size.
//
// The limiter counts requests within a one minute window. When the limit is
// exceeded and Delay is enabled, processing of the request is paused until a
// slot becomes available. Otherwise the request is rejected with HTTP 429.

type SlidingWindowPlugin struct {
	redis   *redis.Client
	window  time.Duration
	perUser int
	global  int
	burst   int
	delay   bool
}

func (s *SlidingWindowPlugin) Name() string  { return "advanced-ratelimit" }
func (s *SlidingWindowPlugin) Priority() int { return 10 }

// Init parses configuration values from the provided map. Expected keys:
// "per_user_limit", "global_limit", "burst", "delay", "window_seconds".
func (s *SlidingWindowPlugin) Init(cfg map[string]interface{}) error {
	s.window = time.Minute
	if v, ok := cfg["window_seconds"].(int); ok && v > 0 {
		s.window = time.Duration(v) * time.Second
	} else if v, ok := cfg["window_seconds"].(float64); ok && v > 0 {
		s.window = time.Duration(int(v)) * time.Second
	}
	if v, ok := cfg["per_user_limit"].(int); ok {
		s.perUser = v
	} else if v, ok := cfg["per_user_limit"].(float64); ok {
		s.perUser = int(v)
	}
	if v, ok := cfg["global_limit"].(int); ok {
		s.global = v
	} else if v, ok := cfg["global_limit"].(float64); ok {
		s.global = int(v)
	}
	if v, ok := cfg["burst"].(int); ok {
		s.burst = v
	} else if v, ok := cfg["burst"].(float64); ok {
		s.burst = int(v)
	}
	if v, ok := cfg["delay"].(bool); ok {
		s.delay = v
	}

	host := os.Getenv("REDIS_HOST")
	if host == "" {
		host = "localhost"
	}
	port := os.Getenv("REDIS_PORT")
	if port == "" {
		port = "6379"
	}
	s.redis = redis.NewClient(&redis.Options{Addr: fmt.Sprintf("%s:%s", host, port)})
	return nil
}

func (s *SlidingWindowPlugin) Process(ctx context.Context, req *http.Request, resp http.ResponseWriter, next http.Handler) {
	user := req.Header.Get("X-User-ID")
	if user == "" {
		user = req.RemoteAddr
	}

	if allowed, wait := s.allow(ctx, "rl:user:"+user, s.perUser); !allowed {
		if s.delay && wait > 0 {
			time.Sleep(wait)
		} else {
			http.Error(resp, "rate limit exceeded", http.StatusTooManyRequests)
			return
		}
	}

	if allowed, wait := s.allow(ctx, "rl:global", s.global); !allowed {
		if s.delay && wait > 0 {
			time.Sleep(wait)
		} else {
			http.Error(resp, "rate limit exceeded", http.StatusTooManyRequests)
			return
		}
	}

	next.ServeHTTP(resp, req)
}

func (s *SlidingWindowPlugin) allow(ctx context.Context, key string, limit int) (bool, time.Duration) {
	if limit <= 0 {
		return true, 0
	}
	now := time.Now()
	start := now.Add(-s.window).UnixNano() / int64(time.Millisecond)
	nowMS := now.UnixNano() / int64(time.Millisecond)

	r := s.redis
	// remove old entries
	r.ZRemRangeByScore(ctx, key, "0", strconv.FormatInt(start, 10))
	count, err := r.ZCard(ctx, key).Result()
	if err != nil {
		return true, 0
	}
	if int(count) >= limit+s.burst {
		// get earliest timestamp to calculate wait time
		vals, err := r.ZRange(ctx, key, 0, 0).Result()
		if err == nil && len(vals) == 1 {
			ts, _ := strconv.ParseInt(vals[0], 10, 64)
			wait := time.Duration(ts+int64(s.window/time.Millisecond)-nowMS) * time.Millisecond
			if wait > 0 {
				return false, wait
			}
		}
		return false, s.window
	}

	r.ZAdd(ctx, key, redis.Z{Score: float64(nowMS), Member: nowMS})
	r.Expire(ctx, key, s.window)
	return true, 0
}
