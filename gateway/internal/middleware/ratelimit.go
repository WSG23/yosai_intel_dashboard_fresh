package middleware

import (
	"context"
	"net/http"
	"os"
	"strconv"
	"time"

        "github.com/WSG23/yosai-gateway/tracing"
        xerrors "github.com/WSG23/errors"
)

// Simple rate limiter using a token bucket.
func RateLimit(next http.Handler) http.Handler {
	bucket := 10
	if v := os.Getenv("RATE_LIMIT_BUCKET"); v != "" {
		if n, err := strconv.Atoi(v); err == nil && n > 0 {
			bucket = n
		}
	}
	interval := 100
	if v := os.Getenv("RATE_LIMIT_INTERVAL_MS"); v != "" {
		if n, err := strconv.Atoi(v); err == nil && n > 0 {
			interval = n
		}
	}

	ticker := time.NewTicker(time.Duration(interval) * time.Millisecond)
	tokens := make(chan struct{}, bucket)

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
                        xerrors.WriteJSON(w, http.StatusTooManyRequests, xerrors.Unavailable, "rate limit exceeded", nil)
		}
	})
}
