package shutdown

import (
	"context"
	"os/signal"
	"syscall"
)

// Notify returns a context that is cancelled when the process receives an interrupt or SIGTERM signal.
// It also returns a stop function to cancel the context manually.
func Notify(parent context.Context) (context.Context, context.CancelFunc) {
	ctx, cancel := signal.NotifyContext(parent, syscall.SIGINT, syscall.SIGTERM)
	return ctx, cancel
}
