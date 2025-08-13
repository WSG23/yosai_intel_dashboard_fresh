package tracing

import (
	"context"
	"testing"
)

func TestTracer(t *testing.T) {
	tr := NewTracer(nil)
	shutdown, err := tr.Start(context.Background(), "test", "")
	if err != nil {
		t.Fatal(err)
	}
	if shutdown == nil {
		t.Fatalf("expected shutdown function")
	}
	if err := shutdown(context.Background()); err != nil {
		t.Fatalf("shutdown: %v", err)
	}
}
