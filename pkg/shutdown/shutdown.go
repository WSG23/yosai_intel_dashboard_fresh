package shutdown

import (
	"context"
	"os"
	"os/signal"
	"syscall"
	"time"
)

// Notify returns a context that is canceled on SIGINT/SIGTERM.
func Notify(parent context.Context) (context.Context, context.CancelFunc) {
	return signal.NotifyContext(parent, os.Interrupt, syscall.SIGTERM)
}

// WithTimeout returns a child context that times out after d.
func WithTimeout(parent context.Context, d time.Duration) (context.Context, context.CancelFunc) {
	return context.WithTimeout(parent, d)
}
