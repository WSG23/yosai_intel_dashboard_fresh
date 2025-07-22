package auth

import (
	"context"

	"github.com/golang-jwt/jwt/v5"
)

// EnhancedClaims adds role and permission information to JWT claims.
type EnhancedClaims struct {
	jwt.RegisteredClaims
	Roles       []string `json:"roles,omitempty"`
	Permissions []string `json:"permissions,omitempty"`
}

// contextKey is used for storing claims in a request context.
type contextKey struct{}

var claimsKey contextKey

// NewContext returns a copy of ctx with the given claims attached.
func NewContext(ctx context.Context, c *EnhancedClaims) context.Context {
	return context.WithValue(ctx, claimsKey, c)
}

// FromContext retrieves claims previously stored with NewContext.
func FromContext(ctx context.Context) (*EnhancedClaims, bool) {
	c, ok := ctx.Value(claimsKey).(*EnhancedClaims)
	return c, ok
}
