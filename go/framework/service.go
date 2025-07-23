package framework

import (
	"context"
	"log"
	"net"
	"net/http"
	"os"
	"os/signal"
	"strings"
	"syscall"
	"time"

	"github.com/prometheus/client_golang/prometheus"
	"github.com/prometheus/client_golang/prometheus/promhttp"
	"go.opentelemetry.io/otel"
	"go.opentelemetry.io/otel/exporters/jaeger"
	"go.opentelemetry.io/otel/propagation"
	sdkresource "go.opentelemetry.io/otel/sdk/resource"
	sdktrace "go.opentelemetry.io/otel/sdk/trace"
	semconv "go.opentelemetry.io/otel/semconv/v1.17.0"
	"go.uber.org/zap"
)

// BaseService provides logging, metrics, tracing and signal handling.
type BaseService struct {
	Name          string
	Config        Config
	ctx           context.Context
	cancel        context.CancelFunc
	logger        *zap.Logger
	registry      *prometheus.Registry
	metricsSrv    *http.Server
	metricsLn     net.Listener
	reqCount      *prometheus.CounterVec
	reqDuration   *prometheus.HistogramVec
	traceShutdown func(context.Context) error
}

func NewBaseService(name, cfgPath string) (*BaseService, error) {
	cfg, err := LoadConfig(cfgPath)
	if err != nil {
		return nil, err
	}
	ctx, cancel := context.WithCancel(context.Background())
	return &BaseService{Name: name, Config: cfg, ctx: ctx, cancel: cancel}, nil
}

func (s *BaseService) Start() {
	s.setupLogging()
	s.setupMetrics()
	s.setupTracing()
	s.handleSignals()
	if s.logger != nil {
		s.logger.Info("service started")
	}
	<-s.ctx.Done()
	if s.logger != nil {
		s.logger.Info("service stopped")
	}
}

func (s *BaseService) Stop() {
	if s.metricsSrv != nil {
		ctx, cancel := context.WithTimeout(context.Background(), time.Second)
		_ = s.metricsSrv.Shutdown(ctx)
		cancel()
	}
	if s.traceShutdown != nil {
		_ = s.traceShutdown(context.Background())
	}
	s.cancel()
}

func (s *BaseService) setupLogging() {
	cfg := zap.NewProductionConfig()
	cfg.OutputPaths = []string{"stdout"}
	level := zap.InfoLevel
	if lvl := strings.ToUpper(s.Config.LogLevel); lvl != "" {
		if parsed, err := zap.ParseAtomicLevel(lvl); err == nil {
			level = parsed.Level()
		}
	}
	cfg.Level = zap.NewAtomicLevelAt(level)
	logger, err := cfg.Build()
	if err != nil {
		log.Printf("failed to init logger: %v", err)
		return
	}
	s.logger = logger.Named(s.Name)
	zap.ReplaceGlobals(s.logger)
}

func (s *BaseService) setupMetrics() {
	if s.Config.MetricsAddr == "" {
		return
	}
	s.registry = prometheus.NewRegistry()
	s.reqCount = prometheus.NewCounterVec(prometheus.CounterOpts{
		Name: "http_requests_total",
		Help: "Total HTTP requests",
	}, []string{"method", "endpoint", "status"})
	s.reqDuration = prometheus.NewHistogramVec(prometheus.HistogramOpts{
		Name:    "http_request_duration_seconds",
		Help:    "HTTP request duration in seconds",
		Buckets: prometheus.DefBuckets,
	}, []string{"method", "endpoint", "status"})
	s.registry.MustRegister(s.reqCount, s.reqDuration)

	mux := http.NewServeMux()
	mux.Handle("/metrics", promhttp.HandlerFor(s.registry, promhttp.HandlerOpts{}))
	s.metricsSrv = &http.Server{Handler: mux}
	ln, err := net.Listen("tcp", s.Config.MetricsAddr)
	if err != nil {
		if s.logger != nil {
			s.logger.Error("metrics listener error", zap.Error(err))
		}
		return
	}
	s.metricsLn = ln
	go func() {
		if err := s.metricsSrv.Serve(ln); err != nil && err != http.ErrServerClosed {
			if s.logger != nil {
				s.logger.Error("metrics server error", zap.Error(err))
			}
		}
	}()
}

func (s *BaseService) setupTracing() {
	endpoint := s.Config.TracingEndpoint
	if endpoint == "" {
		endpoint = "http://localhost:14268/api/traces"
	}
	exp, err := jaeger.New(jaeger.WithCollectorEndpoint(jaeger.WithEndpoint(endpoint)))
	if err != nil {
		if s.logger != nil {
			s.logger.Error("init tracing", zap.Error(err))
		}
		return
	}
	tp := sdktrace.NewTracerProvider(
		sdktrace.WithBatcher(exp),
		sdktrace.WithResource(sdkresource.NewWithAttributes(
			semconv.SchemaURL,
			semconv.ServiceName(s.Config.ServiceName),
		)),
	)
	otel.SetTracerProvider(tp)
	otel.SetTextMapPropagator(propagation.TraceContext{})
	s.traceShutdown = tp.Shutdown
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
