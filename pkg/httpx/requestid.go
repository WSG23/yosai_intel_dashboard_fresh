package httpx

import (
	"context"
	"github.com/google/uuid"
)

// requestIDKey is used for storing the request ID in a context.Context.
type requestIDKey struct{}

// RequestIDHeader is the HTTP header used for propagating request IDs.
const RequestIDHeader = "X-Request-ID"

// WithRequestID returns a new context with the provided request ID attached.
func WithRequestID(ctx context.Context, id string) context.Context {
	return context.WithValue(ctx, requestIDKey{}, id)
}

// RequestIDFromContext extracts the request ID from the context if present.
func RequestIDFromContext(ctx context.Context) (string, bool) {
	v, ok := ctx.Value(requestIDKey{}).(string)
	return v, ok
}

// EnsureRequestID ensures that the context has a request ID, generating a new
// one if necessary. It returns the updated context and the ID.
func EnsureRequestID(ctx context.Context) (context.Context, string) {
	if id, ok := RequestIDFromContext(ctx); ok {
		return ctx, id
	}
	id := uuid.New().String()
	return WithRequestID(ctx, id), id
}
