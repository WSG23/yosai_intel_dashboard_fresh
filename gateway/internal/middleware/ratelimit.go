package middleware

import (
	"context"
	"net/http"
	"time"

	"github.com/WSG23/yosai-gateway/tracing"
)

// Simple rate limiter using a token bucket.
func RateLimit(next http.Handler) http.Handler {
	ticker := time.NewTicker(time.Millisecond * 100)
	tokens := make(chan struct{}, 10)

	go func() {
		tracing.TraceAsyncOperation(context.Background(), "rate_limit_refill", "bucket", func(ctx context.Context) error {
			for range ticker.C {
				select {
				case tokens <- struct{}{}:
				default:
				}
			}
			return nil
		})
	}()

	return http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		select {
		case <-tokens:
			next.ServeHTTP(w, r)
		default:
			http.Error(w, "rate limit exceeded", http.StatusTooManyRequests)
		}
	})
}
