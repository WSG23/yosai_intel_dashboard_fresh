package httpx

import (
	"context"

	"github.com/google/uuid"
)

// correlationIDKey is used for storing the correlation ID in a context.Context.
type correlationIDKey struct{}

// CorrelationIDHeader is the HTTP header used for propagating correlation IDs.
const CorrelationIDHeader = "X-Correlation-ID"

// WithCorrelationID returns a new context with the provided correlation ID attached.
func WithCorrelationID(ctx context.Context, id string) context.Context {
	return context.WithValue(ctx, correlationIDKey{}, id)
}

// CorrelationIDFromContext extracts the correlation ID from the context if present.
func CorrelationIDFromContext(ctx context.Context) (string, bool) {
	v, ok := ctx.Value(correlationIDKey{}).(string)
	return v, ok
}

// EnsureCorrelationID ensures that the context has a correlation ID, generating
// a new one if necessary. It returns the updated context and the ID.
func EnsureCorrelationID(ctx context.Context) (context.Context, string) {
	if id, ok := CorrelationIDFromContext(ctx); ok {
		return ctx, id
	}
	id := uuid.New().String()
	return WithCorrelationID(ctx, id), id
}
