package proxy

import (
	"context"
	"net"
	"net/http"
	"net/http/httptest"
	"net/url"
	"testing"

	"go.opentelemetry.io/otel"
	"go.opentelemetry.io/otel/propagation"
	sdktrace "go.opentelemetry.io/otel/sdk/trace"
)

func TestProxyInjectsTraceHeaders(t *testing.T) {
	var received string
	backend := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		received = r.Header.Get("traceparent")
		w.WriteHeader(http.StatusOK)
	}))
	defer backend.Close()

	u, err := url.Parse(backend.URL)
	if err != nil {
		t.Fatalf("parse url: %v", err)
	}
	host, port, err := net.SplitHostPort(u.Host)
	if err != nil {
		t.Fatalf("split host: %v", err)
	}

	t.Setenv("APP_HOST", host)
	t.Setenv("APP_PORT", port)

	tp := sdktrace.NewTracerProvider()
	otel.SetTracerProvider(tp)
	otel.SetTextMapPropagator(propagation.TraceContext{})
	defer tp.Shutdown(context.Background())

	p, err := NewProxy()
	if err != nil {
		t.Fatalf("new proxy: %v", err)
	}

	ctx, span := otel.Tracer("test").Start(context.Background(), "test")
	defer span.End()

	req := httptest.NewRequest(http.MethodGet, "http://gateway/", nil)
	req = req.WithContext(ctx)

	resp := httptest.NewRecorder()
	p.ServeHTTP(resp, req)

	if resp.Code != http.StatusOK {
		t.Fatalf("expected 200, got %d", resp.Code)
	}
	if received == "" {
		t.Fatal("traceparent header not forwarded")
	}
}
