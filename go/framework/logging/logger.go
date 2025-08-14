package logging

import (
	"context"
	"strings"

	"go.opentelemetry.io/otel/trace"
	"go.uber.org/zap"
)

// Logger abstracts logging implementation.
type Logger interface {
	Info(msg string, fields ...zap.Field)
	Error(msg string, fields ...zap.Field)
}

// ZapLogger is a zap based implementation of Logger.
type ZapLogger struct{ *zap.Logger }

// NewZapLogger creates a named zap logger using the provided level.
func NewZapLogger(name, level string) (*ZapLogger, error) {
	cfg := zap.NewProductionConfig()
	cfg.OutputPaths = []string{"stdout"}
	lvl := zap.InfoLevel
	if v := strings.ToUpper(level); v != "" {
		if parsed, err := zap.ParseAtomicLevel(v); err == nil {
			lvl = parsed.Level()
		}
	}
	cfg.Level = zap.NewAtomicLevelAt(lvl)
	lg, err := cfg.Build()
	if err != nil {
		return nil, err
	}
	return &ZapLogger{lg.Named(name)}, nil
}

func (l *ZapLogger) Info(msg string, fields ...zap.Field)  { l.Logger.Info(msg, fields...) }
func (l *ZapLogger) Error(msg string, fields ...zap.Field) { l.Logger.Error(msg, fields...) }

// Debug writes a debug level log entry.
func (l *ZapLogger) Debug(msg string, fields ...zap.Field) { l.Logger.Debug(msg, fields...) }

const correlationIDKey = "correlation_id"

func contextFields(ctx context.Context) []zap.Field {
	if ctx == nil {
		return nil
	}
	var fields []zap.Field
	if v, ok := ctx.Value(correlationIDKey).(string); ok && v != "" {
		fields = append(fields, zap.String(correlationIDKey, v))
	}
	if span := trace.SpanFromContext(ctx); span != nil {
		sc := span.SpanContext()
		if sc.IsValid() {
			fields = append(fields,
				zap.String("trace_id", sc.TraceID().String()),
				zap.String("span_id", sc.SpanID().String()),
			)
		}
	}
	return fields
}

// InfoContext logs an info message including correlation and tracing data from context.
func (l *ZapLogger) InfoContext(ctx context.Context, msg string, fields ...zap.Field) {
	fields = append(fields, contextFields(ctx)...)
	l.Logger.Info(msg, fields...)
}

// ErrorContext logs an error message including correlation and tracing data from context.
func (l *ZapLogger) ErrorContext(ctx context.Context, msg string, fields ...zap.Field) {
	fields = append(fields, contextFields(ctx)...)
	l.Logger.Error(msg, fields...)
}

// DebugContext logs a debug message including correlation and tracing data from context.
func (l *ZapLogger) DebugContext(ctx context.Context, msg string, fields ...zap.Field) {
	fields = append(fields, contextFields(ctx)...)
	l.Logger.Debug(msg, fields...)
}
