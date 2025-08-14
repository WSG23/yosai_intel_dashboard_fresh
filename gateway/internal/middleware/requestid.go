package middleware

import (
	"net/http"

	httpx "github.com/WSG23/httpx"
)

// RequestID extracts the X-Request-ID header, storing it in the request context
// and ensuring it is set on the request for downstream services.
func RequestID() func(http.Handler) http.Handler {
	return func(next http.Handler) http.Handler {
		return http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
			ctx := r.Context()
			if id := r.Header.Get(httpx.RequestIDHeader); id != "" {
				ctx = httpx.WithRequestID(ctx, id)
			} else {
				var id string
				ctx, id = httpx.EnsureRequestID(ctx)
				r.Header.Set(httpx.RequestIDHeader, id)
			}
			next.ServeHTTP(w, r.WithContext(ctx))
		})
	}
}
