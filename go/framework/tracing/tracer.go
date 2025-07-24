package tracing

import (
	"context"

	"go.opentelemetry.io/otel"
	"go.opentelemetry.io/otel/exporters/jaeger"
	sdkresource "go.opentelemetry.io/otel/sdk/resource"
	sdktrace "go.opentelemetry.io/otel/sdk/trace"
	semconv "go.opentelemetry.io/otel/semconv/v1.17.0"
)

// Tracer configures application tracing and returns a shutdown function.
type Tracer interface {
	Start(serviceName, endpoint string) (func(context.Context) error, error)
}

type JaegerTracer struct{}

func NewJaegerTracer() *JaegerTracer { return &JaegerTracer{} }

func (JaegerTracer) Start(serviceName, endpoint string) (func(context.Context) error, error) {
	if endpoint == "" {
		endpoint = "http://localhost:14268/api/traces"
	}
	exp, err := jaeger.New(jaeger.WithCollectorEndpoint(jaeger.WithEndpoint(endpoint)))
	if err != nil {
		return nil, err
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
