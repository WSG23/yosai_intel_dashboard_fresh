package shutdown

import (
	"context"
	"os"
	"os/signal"
	"syscall"
	"time"
)

// WithTimeout returns a context that is cancelled when the timeout expires or
// when an interrupt or termination signal is received. It returns the derived
// context and a cancel function to release resources.
func WithTimeout(parent context.Context, timeout time.Duration) (context.Context, context.CancelFunc) {
	ctx, cancel := context.WithTimeout(parent, timeout)
	sigCh := make(chan os.Signal, 1)
	signal.Notify(sigCh, os.Interrupt, syscall.SIGTERM)

	go func() {
		select {
		case <-sigCh:
			cancel()
		case <-ctx.Done():
		}
		signal.Stop(sigCh)
		close(sigCh)
	}()

	return ctx, cancel
}
