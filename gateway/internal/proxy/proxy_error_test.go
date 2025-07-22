package proxy

import (
    "os"
    "testing"
)

func TestNewProxyInvalidPort(t *testing.T) {
    os.Setenv("APP_PORT", "badport")
    os.Unsetenv("APP_HOST")
    if _, err := NewProxy(); err == nil {
        t.Fatal("expected error")
    }
}
