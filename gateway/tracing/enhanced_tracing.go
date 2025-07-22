package tracing

import (
	"context"

	"go.opentelemetry.io/otel"
	"go.opentelemetry.io/otel/attribute"
	"go.opentelemetry.io/otel/trace"
)

type EnhancedTracer struct {
	tracer trace.Tracer
}

func NewEnhancedTracer() *EnhancedTracer {
	return &EnhancedTracer{tracer: otel.Tracer("async-operations")}
}

func (et *EnhancedTracer) TraceAsyncOperation(ctx context.Context, name string, taskID string, fn func(context.Context) error) error {
	ctx, span := et.tracer.Start(context.Background(), name, trace.WithAttributes(attribute.String("task.id", taskID)))
	defer span.End()
	err := fn(ctx)
	if err != nil {
		span.RecordError(err)
	}
	return err
}
