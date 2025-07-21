package middleware

import (
	"net/http"
	"time"
)

// Simple rate limiter using a token bucket.
func RateLimit(next http.Handler) http.Handler {
	ticker := time.NewTicker(time.Millisecond * 100)
	tokens := make(chan struct{}, 10)

	go func() {
		for range ticker.C {
			select {
			case tokens <- struct{}{}:
			default:
			}
		}
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
