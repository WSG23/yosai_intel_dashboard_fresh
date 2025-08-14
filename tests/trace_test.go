package tests

import (
	"context"
	"net/http"
	"net/http/httptest"
	"testing"

	httpx "github.com/WSG23/httpx"
	"go.opentelemetry.io/contrib/instrumentation/net/http/otelhttp"
	"go.opentelemetry.io/otel"
	sdkresource "go.opentelemetry.io/otel/sdk/resource"
	sdktrace "go.opentelemetry.io/otel/sdk/trace"
	"go.opentelemetry.io/otel/sdk/trace/tracetest"
	semconv "go.opentelemetry.io/otel/semconv/v1.17.0"
)

// TestHTTPTracing verifies that spans are exported for client and server calls.
func TestHTTPTracing(t *testing.T) {
	sr := tracetest.NewSpanRecorder()
	tp := sdktrace.NewTracerProvider(
		sdktrace.WithSpanProcessor(sr),
		sdktrace.WithResource(sdkresource.NewWithAttributes(
			semconv.SchemaURL,
			semconv.ServiceName("trace-test"),
		)),
	)
	otel.SetTracerProvider(tp)
	defer func() { _ = tp.Shutdown(context.Background()) }()

	handler := otelhttp.NewHandler(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		w.Header().Set("Content-Type", "application/json")
		w.Write([]byte(`{"status":"ok"}`))
	}), "server")
	srv := httptest.NewServer(handler)
	defer srv.Close()

	client := httpx.New(&http.Client{Transport: otelhttp.NewTransport(http.DefaultTransport)})
	req, err := http.NewRequest(http.MethodGet, srv.URL, nil)
	if err != nil {
		t.Fatalf("new request: %v", err)
	}
	var resp map[string]string
	if err := client.DoJSON(context.Background(), req, &resp); err != nil {
		t.Fatalf("DoJSON: %v", err)
	}

	if len(sr.Ended()) < 2 {
		t.Fatalf("expected spans to be recorded")
	}
}
