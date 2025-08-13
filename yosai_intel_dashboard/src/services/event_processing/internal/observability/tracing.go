package observability

import (
    "context"
    "log"
    "os"

    "go.opentelemetry.io/otel"
    "go.opentelemetry.io/otel/attribute"
    "go.opentelemetry.io/otel/exporters/otlp/otlptrace/otlptracehttp"
    "go.opentelemetry.io/otel/sdk/resource"
    "go.opentelemetry.io/otel/sdk/trace"
)

// InitTracer configures an OTLP HTTP exporter and registers the tracer provider.
func InitTracer(ctx context.Context, service string) (*trace.TracerProvider, error) {
    endpoint := os.Getenv("OTEL_EXPORTER_OTLP_ENDPOINT")
    exp, err := otlptracehttp.New(ctx, otlptracehttp.WithEndpoint(endpoint), otlptracehttp.WithInsecure())
    if err != nil {
        return nil, err
    }

    tp := trace.NewTracerProvider(
        trace.WithBatcher(exp),
        trace.WithResource(resource.NewWithAttributes(
            attribute.String("service.name", service),
        )),
    )
    otel.SetTracerProvider(tp)
    return tp, nil
}

// Shutdown flushes and shuts down the tracer provider.
func Shutdown(ctx context.Context, tp *trace.TracerProvider) {
    if err := tp.Shutdown(ctx); err != nil {
        log.Printf("tracer shutdown: %v", err)
    }
}

