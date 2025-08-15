package logging

import (
	"context"
	"strings"

	httpx "github.com/WSG23/httpx"
	"go.uber.org/zap"
	"go.uber.org/zap/zapcore"
)

// Logger abstracts logging implementation.
type Logger interface {
	Info(ctx context.Context, msg string, fields ...zap.Field)
	Error(ctx context.Context, msg string, fields ...zap.Field)
}

// ZapLogger is a zap based implementation of Logger.
type ZapLogger struct{ *zap.Logger }

// NewZapLogger creates a named zap logger using the provided level.
func NewZapLogger(name, level string) (*ZapLogger, error) {
	cfg := zap.NewProductionConfig()
	cfg.OutputPaths = []string{"stdout"}
	cfg.EncoderConfig = zapcore.EncoderConfig{
		TimeKey:      "time",
		LevelKey:     "level",
		NameKey:      "logger",
		CallerKey:    "caller",
		MessageKey:   "msg",
		EncodeTime:   zapcore.ISO8601TimeEncoder,
		EncodeLevel:  zapcore.LowercaseLevelEncoder,
		EncodeCaller: zapcore.ShortCallerEncoder,
	}
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
	lg = lg.With(zap.String("service", name))
	return &ZapLogger{lg}, nil
}

func withCorrelation(ctx context.Context, fields []zap.Field) []zap.Field {
	if cid, ok := httpx.CorrelationIDFromContext(ctx); ok {
		fields = append(fields, zap.String("correlation_id", cid))
	}
	return fields
}

func (l *ZapLogger) Info(ctx context.Context, msg string, fields ...zap.Field) {
	l.Logger.Info(msg, withCorrelation(ctx, fields)...)
}

func (l *ZapLogger) Error(ctx context.Context, msg string, fields ...zap.Field) {
	l.Logger.Error(msg, withCorrelation(ctx, fields)...)
}
