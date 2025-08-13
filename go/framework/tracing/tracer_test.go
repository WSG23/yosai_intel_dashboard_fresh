package tracing

import "testing"

func TestOTLPTracer(t *testing.T) {
	jt := NewOTLPTracer()
	shutdown, err := jt.Start("test", "")
	if err != nil {
		t.Fatal(err)
	}
	if shutdown == nil {
		t.Fatalf("expected shutdown function")
	}
}
