package logging

import (
	"strings"

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
