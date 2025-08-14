package middleware

import (
	"context"
	"net"
	"net/http"
	"strconv"
	"time"

	"github.com/redis/go-redis/v9"

	gwconfig "github.com/WSG23/yosai-gateway/internal/config"
	serrors "github.com/WSG23/yosai_intel_dashboard_fresh/shared/errors"
)

type RateLimiter struct {
	redis  *redis.Client
	cfg    gwconfig.RateLimitSettings
	window time.Duration
}

func NewRateLimiter(rdb *redis.Client, cfg gwconfig.RateLimitSettings) *RateLimiter {
	if cfg.Burst < 0 {
		cfg.Burst = 0
	}
	return &RateLimiter{redis: rdb, cfg: cfg, window: time.Minute}
}

// SetWindow overrides the default refill window.
func (rl *RateLimiter) SetWindow(d time.Duration) {
	if d > 0 {
		rl.window = d
	}
}

func (rl *RateLimiter) take(key string, limit int) (bool, int, time.Duration) {
	if limit <= 0 {
		return true, -1, 0
	}
	ctx := context.Background()
	cnt, err := rl.redis.Incr(ctx, key).Result()
	if err != nil {
		return true, -1, 0
	}
	if cnt == 1 {
		rl.redis.Expire(ctx, key, rl.window)
	}
	remaining := limit + rl.cfg.Burst - int(cnt)
	ttl, err := rl.redis.TTL(ctx, key).Result()
	if err != nil || ttl < 0 {
		ttl = rl.window
	}
	if remaining < 0 {
		return false, remaining, ttl
	}
	return true, remaining, ttl
}

func (rl *RateLimiter) Allow(r *http.Request) (bool, int, time.Duration) {
	var minRemaining int = int(^uint(0) >> 1)
	var ttl time.Duration
	ip, _, _ := net.SplitHostPort(r.RemoteAddr)
	allowed, rem, t := rl.take("rl:ip:"+ip, rl.cfg.PerIP)
	if !allowed {
		return false, rem, t
	}
	if rem >= 0 && rem < minRemaining {
		minRemaining, ttl = rem, t
	}
	if user := r.Header.Get("X-User-ID"); user != "" {
		allowed, rem, t = rl.take("rl:user:"+user, rl.cfg.PerUser)
		if !allowed {
			return false, rem, t
		}
		if rem >= 0 && rem < minRemaining {
			minRemaining, ttl = rem, t
		}
	}
	if key := r.Header.Get("X-API-Key"); key != "" {
		allowed, rem, t = rl.take("rl:key:"+key, rl.cfg.PerKey)
		if !allowed {
			return false, rem, t
		}
		if rem >= 0 && rem < minRemaining {
			minRemaining, ttl = rem, t
		}
	}
	allowed, rem, t = rl.take("rl:global", rl.cfg.Global)
	if !allowed {
		return false, rem, t
	}
	if rem >= 0 && rem < minRemaining {
		minRemaining, ttl = rem, t
	}
	if minRemaining == int(^uint(0)>>1) {
		minRemaining = -1
		ttl = rl.window
	}
	return true, minRemaining, ttl
}

func (rl *RateLimiter) Middleware(next http.Handler) http.Handler {
	return http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		if r.URL.Path == "/health" || r.URL.Path == "/metrics" {
			next.ServeHTTP(w, r)
			return
		}
		allowed, remaining, ttl := rl.Allow(r)
		limit := rl.cfg.Global
		if limit <= 0 {
			limit = rl.cfg.PerUser
		}
		if limit <= 0 {
			limit = rl.cfg.PerIP
		}
		if limit <= 0 {
			limit = rl.cfg.PerKey
		}
		w.Header().Set("X-RateLimit-Limit", strconv.Itoa(limit))
		if remaining >= 0 {
			w.Header().Set("X-RateLimit-Remaining", strconv.Itoa(remaining))
		}
		if ttl > 0 {
			w.Header().Set("X-RateLimit-Reset", strconv.Itoa(int(ttl.Seconds())))
		}
		if !allowed {
			serrors.WriteJSON(w, http.StatusTooManyRequests, serrors.Unavailable, "rate limit exceeded", nil)
			return
		}
		next.ServeHTTP(w, r)
	})
}
