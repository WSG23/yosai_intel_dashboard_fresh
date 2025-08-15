package shutdown

import (
        "context"
        "os"
        "syscall"
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

func TestNotify(t *testing.T) {
        ctx, cancel := Notify(context.Background())
        defer cancel()

        // Send SIGTERM to current process to trigger cancellation.
        if err := syscall.Kill(os.Getpid(), syscall.SIGTERM); err != nil {
                t.Fatalf("kill: %v", err)
        }

        select {
        case <-ctx.Done():
                // ok
        case <-time.After(50 * time.Millisecond):
                t.Fatal("expected context to cancel on signal")
        }
}
