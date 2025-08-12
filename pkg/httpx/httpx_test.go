package httpx

import (
    "context"
    "net/http"
    "testing"
    "time"
)

func TestDefaultClientTimeout(t *testing.T) {
    if DefaultClient.Timeout == 0 {
        t.Fatal("expected non-zero client timeout")
    }
}

func TestDoJSON_ContextCancel(t *testing.T) {
    req, _ := http.NewRequest("GET", "http://127.0.0.1:0/never", nil) // invalid port ⇒ fast fail
    ctx, cancel := context.WithTimeout(context.Background(), 10*time.Millisecond)
    defer cancel()
    var dst map[string]any
    if err := DoJSON(ctx, req, &dst); err == nil {
        t.Fatal("expected error for unreachable host or timeout")
    }
}

