package framework

import (
	"context"

	"github.com/WSG23/yosai-framework/health"
	"github.com/WSG23/yosai-framework/logging"
	"github.com/WSG23/yosai-framework/metrics"
	"github.com/WSG23/yosai-framework/tracing"
)

// ServiceBuilder assembles service components.
type ServiceBuilder struct {
	name    string
	cfg     Config
	logger  logging.Logger
	metrics metrics.MetricsCollector
	tracer  tracing.Tracer
	health  *health.HealthManager
}

func NewServiceBuilder(name, cfgPath string) (*ServiceBuilder, error) {
	var cfg Config
	var err error
	if cfgPath != "" {
		cfg, err = LoadConfig(cfgPath)
		if err != nil {
			return nil, err
		}
	}
	return &ServiceBuilder{name: name, cfg: cfg}, nil
}

func (b *ServiceBuilder) WithLogger(l logging.Logger) *ServiceBuilder { b.logger = l; return b }
func (b *ServiceBuilder) WithMetrics(m metrics.MetricsCollector) *ServiceBuilder {
	b.metrics = m
	return b
}
func (b *ServiceBuilder) WithTracer(t tracing.Tracer) *ServiceBuilder        { b.tracer = t; return b }
func (b *ServiceBuilder) WithHealth(h *health.HealthManager) *ServiceBuilder { b.health = h; return b }

// Build assembles the components and returns a BaseService.
func (b *ServiceBuilder) Build() (*BaseService, error) {
	if b.health == nil {
		b.health = health.NewManager()
	}
	if b.logger == nil {
		lg, err := logging.NewZapLogger(b.name, b.cfg.LogLevel)
		if err != nil {
			return nil, err
		}
		b.logger = lg
	}
	if b.metrics == nil && b.cfg.MetricsAddr != "" {
		b.metrics = metrics.NewPrometheusCollector(b.cfg.MetricsAddr, b.health, b.logger)
	}
	if b.tracer == nil {
		b.tracer = tracing.NewTracer(nil)
	}

	ctx, cancel := context.WithCancel(context.Background())
	return &BaseService{
		Name:    b.name,
		Config:  b.cfg,
		ctx:     ctx,
		cancel:  cancel,
		Logger:  b.logger,
		Metrics: b.metrics,
		Health:  b.health,
		tracer:  b.tracer,
	}, nil
}
