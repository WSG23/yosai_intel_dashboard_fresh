package tracing

import "testing"

func TestJaegerTracer(t *testing.T) {
	jt := NewJaegerTracer()
	shutdown, err := jt.Start("test", "")
	if err != nil {
		t.Fatal(err)
	}
	if shutdown == nil {
		t.Fatalf("expected shutdown function")
	}
}
