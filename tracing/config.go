package tracing

import (
	"context"
	"os"

	"go.opentelemetry.io/otel"
	"go.opentelemetry.io/otel/exporters/otlp/otlptrace"
	"go.opentelemetry.io/otel/exporters/otlp/otlptrace/otlptracehttp"
	"go.opentelemetry.io/otel/propagation"
	sdkresource "go.opentelemetry.io/otel/sdk/resource"
	sdktrace "go.opentelemetry.io/otel/sdk/trace"
	semconv "go.opentelemetry.io/otel/semconv/v1.17.0"
)

// Init sets up OpenTelemetry tracing with an OTLP HTTP exporter.
// The collector endpoint is read from the OTEL_EXPORTER_OTLP_ENDPOINT
// environment variable. An optional span processor can be provided for
// testing; when nil a batch span processor is configured.
func Init(ctx context.Context, serviceName string, sp sdktrace.SpanProcessor) (func(context.Context) error, error) {
	var opts []sdktrace.TracerProviderOption
	if sp != nil {
		opts = append(opts, sdktrace.WithSpanProcessor(sp))
	} else {
		endpoint := os.Getenv("OTEL_EXPORTER_OTLP_ENDPOINT")
		clientOpts := []otlptracehttp.Option{}
		if endpoint != "" {
			clientOpts = append(clientOpts, otlptracehttp.WithEndpoint(endpoint), otlptracehttp.WithInsecure())
		}
		exp, err := otlptrace.New(ctx, otlptracehttp.NewClient(clientOpts...))
		if err != nil {
			return nil, err
		}
		opts = append(opts, sdktrace.WithBatcher(exp))
	}
	opts = append(opts, sdktrace.WithResource(sdkresource.NewWithAttributes(
		semconv.SchemaURL,
		semconv.ServiceName(serviceName),
	)))
	tp := sdktrace.NewTracerProvider(opts...)
	otel.SetTracerProvider(tp)
	otel.SetTextMapPropagator(propagation.TraceContext{})
	return tp.Shutdown, nil
}
