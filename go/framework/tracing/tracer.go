package tracing

import (
	"context"
	"fmt"

	"go.opentelemetry.io/otel"
	"go.opentelemetry.io/otel/exporters/otlp/otlptrace"
	"go.opentelemetry.io/otel/exporters/otlp/otlptrace/otlptracehttp"
	sdkresource "go.opentelemetry.io/otel/sdk/resource"
	sdktrace "go.opentelemetry.io/otel/sdk/trace"
	semconv "go.opentelemetry.io/otel/semconv/v1.17.0"
)

// Tracer configures application tracing and returns a shutdown function.
type Tracer interface {
	Start(ctx context.Context, serviceName, endpoint string) (func(context.Context) error, error)
}

// OTLPTracer implements Tracer using the OTLP HTTP exporter.
type OTLPTracer struct {
	client otlptrace.Client
}

// NewTracer constructs an OTLPTracer. If client is nil, a default HTTP client is used.
func NewTracer(client otlptrace.Client) *OTLPTracer { return &OTLPTracer{client: client} }

// Start configures tracing and returns a shutdown function.
func (t *OTLPTracer) Start(ctx context.Context, serviceName, endpoint string) (func(context.Context) error, error) {
	if t.client == nil {
		opts := []otlptracehttp.Option{}
		if endpoint != "" {
			opts = append(opts, otlptracehttp.WithEndpoint(endpoint), otlptracehttp.WithInsecure())
		}
		t.client = otlptracehttp.NewClient(opts...)
	}
	exp, err := otlptrace.New(ctx, t.client)
	if err != nil {
		return nil, fmt.Errorf("create exporter: %w", err)
	}
	tp := sdktrace.NewTracerProvider(
		sdktrace.WithBatcher(exp),
		sdktrace.WithResource(sdkresource.NewWithAttributes(
			semconv.SchemaURL,
			semconv.ServiceName(serviceName),
		)),
	)
	otel.SetTracerProvider(tp)
	return tp.Shutdown, nil
}
