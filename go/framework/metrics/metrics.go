package metrics

import (
	"context"
	"net"
	"net/http"

	"github.com/prometheus/client_golang/prometheus"
	"github.com/prometheus/client_golang/prometheus/promhttp"

	"go.uber.org/zap"

	"github.com/WSG23/yosai-framework/health"
	"github.com/WSG23/yosai-framework/logging"
)

// MetricsCollector represents metrics functionality for a service.
type MetricsCollector interface {
	Start() error
	Stop(ctx context.Context) error
	ListenerAddr() string
	Requests() *prometheus.CounterVec
	Durations() *prometheus.HistogramVec
	Errors() *prometheus.CounterVec
}

type PrometheusCollector struct {
	Addr      string
	registry  *prometheus.Registry
	reqCount  *prometheus.CounterVec
	reqDur    *prometheus.HistogramVec
	reqErr    *prometheus.CounterVec
	srv       *http.Server
	ln        net.Listener
	healthMgr *health.HealthManager
	logger    logging.Logger
}

// NewPrometheusCollector creates a Prometheus metrics collector bound to addr.
func NewPrometheusCollector(addr string, hm *health.HealthManager, lg logging.Logger) *PrometheusCollector {
	return &PrometheusCollector{Addr: addr, healthMgr: hm, logger: lg}
}

func (p *PrometheusCollector) init() error {
	p.registry = prometheus.NewRegistry()
	p.reqCount = prometheus.NewCounterVec(prometheus.CounterOpts{
		Name: "yosai_request_total",
		Help: "Total HTTP requests",
	}, []string{"method", "endpoint", "status"})
	p.reqDur = prometheus.NewHistogramVec(prometheus.HistogramOpts{
		Name:    "yosai_request_duration_seconds",
		Help:    "HTTP request duration in seconds",
		Buckets: prometheus.DefBuckets,
	}, []string{"method", "endpoint", "status"})
	p.reqErr = prometheus.NewCounterVec(prometheus.CounterOpts{
		Name: "yosai_error_total",
		Help: "Total errors encountered",
	}, []string{"endpoint"})
	p.registry.MustRegister(p.reqCount, p.reqDur, p.reqErr)
	mux := http.NewServeMux()
	mux.Handle("/metrics", promhttp.HandlerFor(p.registry, promhttp.HandlerOpts{}))
	if p.healthMgr != nil {
		mux.HandleFunc("/health", p.healthMgr.Handler)
		mux.HandleFunc("/health/live", p.healthMgr.LiveHandler)
		mux.HandleFunc("/health/ready", p.healthMgr.ReadyHandler)
		mux.HandleFunc("/health/startup", p.healthMgr.StartupHandler)
	}
	p.srv = &http.Server{Handler: mux}
	ln, err := net.Listen("tcp", p.Addr)
	if err != nil {
		return err
	}
	p.ln = ln
	return nil
}

func (p *PrometheusCollector) Start() error {
	if p.Addr == "" {
		return nil
	}
	if err := p.init(); err != nil {
		if p.logger != nil {
			p.logger.Error("metrics listener error", zap.Error(err))
		}
		return err
	}
	go func() {
		if err := p.srv.Serve(p.ln); err != nil && err != http.ErrServerClosed {
			if p.logger != nil {
				p.logger.Error("metrics server error", zap.Error(err))
			}
		}
	}()
	return nil
}

func (p *PrometheusCollector) Stop(ctx context.Context) error {
	if p.srv != nil {
		return p.srv.Shutdown(ctx)
	}
	return nil
}

func (p *PrometheusCollector) ListenerAddr() string {
	if p.ln != nil {
		return p.ln.Addr().String()
	}
	return ""
}

func (p *PrometheusCollector) Requests() *prometheus.CounterVec    { return p.reqCount }
func (p *PrometheusCollector) Durations() *prometheus.HistogramVec { return p.reqDur }
func (p *PrometheusCollector) Errors() *prometheus.CounterVec      { return p.reqErr }
