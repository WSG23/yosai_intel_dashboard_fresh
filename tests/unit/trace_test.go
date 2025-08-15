package tests

import (
	"context"
	"net/http"
	"net/http/httptest"
	"testing"

	"github.com/WSG23/httpx"
	"github.com/stretchr/testify/require"
	"go.opentelemetry.io/contrib/instrumentation/net/http/otelhttp"
	"go.opentelemetry.io/otel"
	"go.opentelemetry.io/otel/propagation"
	"go.opentelemetry.io/otel/sdk/trace"
	"go.opentelemetry.io/otel/sdk/trace/tracetest"
)

func TestHTTPTracing(t *testing.T) {
	sr := tracetest.NewSpanRecorder()
	tp := trace.NewTracerProvider(trace.WithSpanProcessor(sr))
	otel.SetTracerProvider(tp)
	otel.SetTextMapPropagator(propagation.TraceContext{})
	defer tp.Shutdown(context.Background())

	srv := httptest.NewServer(otelhttp.NewHandler(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		w.Header().Set("Content-Type", "application/json")
		_, _ = w.Write([]byte(`{"ok":true}`))
	}), "test-server"))
	defer srv.Close()

	req, err := http.NewRequest("GET", srv.URL, nil)
	require.NoError(t, err)
	var resp map[string]bool
	err = httpx.Default.DoJSON(context.Background(), req, &resp)
	require.NoError(t, err)

	spans := sr.Ended()
	require.GreaterOrEqual(t, len(spans), 2)
	require.Equal(t, spans[0].SpanContext().TraceID(), spans[1].SpanContext().TraceID())
}
