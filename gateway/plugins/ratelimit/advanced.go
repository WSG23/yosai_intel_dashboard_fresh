package ratelimit

import (
	"context"
	"fmt"
	"net/http"
	"sync"
	"time"

	"github.com/redis/go-redis/v9"
	"golang.org/x/time/rate"
)

type RateLimitRule struct {
	Path        string
	Method      string
	LimitPerMin int
	Burst       int
}

type RateLimitPlugin struct {
	redis    *redis.Client
	limiters sync.Map
	rules    []RateLimitRule
}

func (r *RateLimitPlugin) Name() string                             { return "advanced-rate-limit" }
func (r *RateLimitPlugin) Priority() int                            { return 10 }
func (r *RateLimitPlugin) Init(config map[string]interface{}) error { return nil }

func (r *RateLimitPlugin) limiter(key string, rule RateLimitRule) *rate.Limiter {
	val, ok := r.limiters.Load(key)
	if ok {
		return val.(*rate.Limiter)
	}
	l := rate.NewLimiter(rate.Every(time.Minute/time.Duration(rule.LimitPerMin)), rule.Burst)
	r.limiters.Store(key, l)
	return l
}

func (r *RateLimitPlugin) Process(ctx context.Context, req *http.Request, resp http.ResponseWriter, next http.Handler) {
	var matched *RateLimitRule
	for _, rule := range r.rules {
		if rule.Path == req.URL.Path && (rule.Method == "" || rule.Method == req.Method) {
			matched = &rule
			break
		}
	}
	if matched == nil {
		next.ServeHTTP(resp, req)
		return
	}
	key := fmt.Sprintf("%s:%s", req.RemoteAddr, matched.Path)
	limiter := r.limiter(key, *matched)
	if !limiter.Allow() {
		http.Error(resp, "rate limit exceeded", http.StatusTooManyRequests)
		return
	}
	next.ServeHTTP(resp, req)
}
