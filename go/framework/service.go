package framework

import (
	"context"
	"os"
	"os/signal"
	"syscall"
	"time"

	"github.com/WSG23/yosai-framework/health"
	"github.com/WSG23/yosai-framework/logging"
	"github.com/WSG23/yosai-framework/metrics"
	"github.com/WSG23/yosai-framework/tracing"
	"go.uber.org/zap"
)

// BaseService composes common service components.
type BaseService struct {
	Name   string
	Config Config
	ctx    context.Context
	cancel context.CancelFunc

	Logger  logging.Logger
	Metrics metrics.MetricsCollector
	Health  *health.HealthManager
	tracer  tracing.Tracer

	traceShutdown func(context.Context) error
}

func NewBaseService(name, cfgPath string) (*BaseService, error) {
	b, err := NewServiceBuilder(name, cfgPath)
	if err != nil {
		return nil, err
	}
	return b.Build()
}

// Start runs the configured components and waits for termination signals.
func (s *BaseService) Start() {
	if s.Metrics != nil {
		_ = s.Metrics.Start()
	}
	if s.tracer != nil {
		shutdown, err := s.tracer.Start(s.Config.ServiceName, s.Config.TracingEndpoint)
		if err == nil {
			s.traceShutdown = shutdown
		} else if s.Logger != nil {
			s.Logger.Error("init tracing", zap.Error(err))
		}
	}
	s.Health.SetStartupComplete(true)
	s.Health.SetReady(true)
	s.Health.SetLive(true)
	s.handleSignals()
	if s.Logger != nil {
		s.Logger.Info("service started")
	}
	<-s.ctx.Done()
	if s.Logger != nil {
		s.Logger.Info("service stopped")
	}
}

// Stop shuts down service components.
func (s *BaseService) Stop() {
	if s.Metrics != nil {
		ctx, cancel := context.WithTimeout(context.Background(), time.Second)
		_ = s.Metrics.Stop(ctx)
		cancel()
	}
	if s.traceShutdown != nil {
		_ = s.traceShutdown(context.Background())
	}
	s.Health.SetReady(false)
	s.Health.SetLive(false)
	s.cancel()
}

func (s *BaseService) handleSignals() {
	ch := make(chan os.Signal, 1)
	signal.Notify(ch, syscall.SIGTERM, syscall.SIGINT)
	go func() {
		<-ch
		if s.traceShutdown != nil {
			_ = s.traceShutdown(context.Background())
		}
		s.Stop()
	}()
}
