package shutdown

import (
	"context"
	"testing"
	"time"
)

func TestWithTimeout(t *testing.T) {
	ctx, cancel := WithTimeout(context.Background(), 5*time.Millisecond)
	defer cancel()
	select {
	case <-ctx.Done():
		// ok
	case <-time.After(50 * time.Millisecond):
		t.Fatal("expected timeout to fire")
	}
}
