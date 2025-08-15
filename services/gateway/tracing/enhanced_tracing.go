package tracing

import (
	"context"

	"go.opentelemetry.io/otel"
	"go.opentelemetry.io/otel/attribute"
	"go.opentelemetry.io/otel/propagation"
	"go.opentelemetry.io/otel/trace"
)

var asyncTracer = otel.Tracer("async-operations")

// PropagateContext injects the trace context from ctx into the provided carrier.
func PropagateContext(ctx context.Context, carrier propagation.TextMapCarrier) {
	otel.GetTextMapPropagator().Inject(ctx, carrier)
}

// TraceAsyncOperation runs fn within a new span that is a child of ctx.
// A task.id attribute is attached to the span for easier correlation.
func TraceAsyncOperation(ctx context.Context, name, taskID string, fn func(context.Context) error) error {
	spanCtx := trace.SpanFromContext(ctx)
	ctx = trace.ContextWithSpan(context.Background(), spanCtx)
	ctx, span := asyncTracer.Start(ctx, name, trace.WithAttributes(attribute.String("task.id", taskID)))
	defer span.End()

	if err := fn(ctx); err != nil {
		span.RecordError(err)
		return err
	}
	return nil
}
