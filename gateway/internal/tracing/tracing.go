package tracing

import (
	"context"
	"os"
	"strings"

	"github.com/WSG23/yosai-framework/logging"
	"go.opentelemetry.io/otel"
	"go.opentelemetry.io/otel/exporters/jaeger"
	zipkin "go.opentelemetry.io/otel/exporters/zipkin"
	"go.opentelemetry.io/otel/propagation"
	sdkresource "go.opentelemetry.io/otel/sdk/resource"
	sdktrace "go.opentelemetry.io/otel/sdk/trace"
	semconv "go.opentelemetry.io/otel/semconv/v1.17.0"
	"go.uber.org/zap"
)

const (
	ExporterEnv           = "TRACING_EXPORTER"
	JaegerEndpointEnv     = "JAEGER_ENDPOINT"
	ZipkinEndpointEnv     = "ZIPKIN_ENDPOINT"
	DefaultJaegerEndpoint = "http://localhost:14268/api/traces"
	DefaultZipkinEndpoint = "http://localhost:9411/api/v2/spans"
	ServiceVersionEnv     = "SERVICE_VERSION"
	EnvironmentEnv        = "APP_ENV"
)

// Logger is the structured logger used across gateway services.
var (
	Logger             *logging.ZapLogger
	serviceVersion     string
	serviceEnvironment string
	serviceName        string
)

// InitTracing configures OpenTelemetry with a Jaeger or Zipkin exporter and returns
// a shutdown function to flush spans.
func InitTracing(name string) (func(context.Context) error, error) {
	serviceName = name
	exporter := strings.ToLower(os.Getenv(ExporterEnv))
	var (
		endpoint string
		err      error
		exp      sdktrace.SpanExporter
	)
	if exporter == "zipkin" {
		endpoint = os.Getenv(ZipkinEndpointEnv)
		if endpoint == "" {
			endpoint = DefaultZipkinEndpoint
		}
		exp, err = zipkin.New(endpoint)
	} else {
		endpoint = os.Getenv(JaegerEndpointEnv)
		if endpoint == "" {
			endpoint = DefaultJaegerEndpoint
		}
		exp, err = jaeger.New(jaeger.WithCollectorEndpoint(jaeger.WithEndpoint(endpoint)))
	}
	if err != nil {
		return nil, err
	}
	serviceVersion = os.Getenv(ServiceVersionEnv)
	if serviceVersion == "" {
		serviceVersion = "0.0.0"
	}
	serviceEnvironment = os.Getenv(EnvironmentEnv)
	if serviceEnvironment == "" {
		serviceEnvironment = "development"
	}
	tp := sdktrace.NewTracerProvider(
		sdktrace.WithBatcher(exp),
		sdktrace.WithResource(sdkresource.NewWithAttributes(
			semconv.SchemaURL,
			semconv.ServiceName(serviceName),
		)),
	)
	otel.SetTracerProvider(tp)
	otel.SetTextMapPropagator(propagation.TraceContext{})

	lg, err := logging.NewZapLogger(serviceName, "INFO")
	if err != nil {
		return nil, err
	}
	lg.Logger = lg.Logger.With(
		zap.String("service", serviceName),
		zap.String("service_version", serviceVersion),
		zap.String("environment", serviceEnvironment),
	)
	Logger = lg

	return tp.Shutdown, nil
}
