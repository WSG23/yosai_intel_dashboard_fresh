package tracing

import (
	"context"
	"os"
	"strings"

	"go.opentelemetry.io/otel"
	"go.opentelemetry.io/otel/exporters/jaeger"
	otlptracehttp "go.opentelemetry.io/otel/exporters/otlp/otlptrace/otlptracehttp"
	"go.opentelemetry.io/otel/propagation"
	sdkresource "go.opentelemetry.io/otel/sdk/resource"
	sdktrace "go.opentelemetry.io/otel/sdk/trace"
	semconv "go.opentelemetry.io/otel/semconv/v1.17.0"
	"go.opentelemetry.io/otel/trace"

	httpx "github.com/WSG23/httpx"
	"github.com/sirupsen/logrus"
)

const (
	ExporterEnv           = "TRACING_EXPORTER"
	JaegerEndpointEnv     = "JAEGER_ENDPOINT"
	OTLPEndpointEnv       = "OTLP_ENDPOINT"
	DefaultJaegerEndpoint = "http://localhost:14268/api/traces"
	DefaultOTLPEndpoint   = "http://localhost:4318/v1/traces"
	ServiceVersionEnv     = "SERVICE_VERSION"
	EnvironmentEnv        = "APP_ENV"
)

// Logger is the structured logger used across gateway services.
var (
	Logger             = logrus.New()
	serviceVersion     string
	serviceEnvironment string
	serviceName        string
)

type traceFormatter struct {
	logrus.JSONFormatter
}

func (f *traceFormatter) Format(entry *logrus.Entry) ([]byte, error) {
	if entry.Context != nil {
		span := trace.SpanFromContext(entry.Context)
		sc := span.SpanContext()
		if sc.IsValid() {
			entry.Data["trace_id"] = sc.TraceID().String()
			entry.Data["span_id"] = sc.SpanID().String()
		}
		if cid, ok := httpx.CorrelationIDFromContext(entry.Context); ok {
			entry.Data["correlation_id"] = cid
		}
	}
	if entry.Data["service"] == nil {
		entry.Data["service"] = serviceName
	}
	entry.Data["service_version"] = serviceVersion
	entry.Data["environment"] = serviceEnvironment
	return f.JSONFormatter.Format(entry)
}

// InitTracing configures OpenTelemetry with a Jaeger or OTLP exporter and returns
// a shutdown function to flush spans.
func InitTracing(name string) (func(context.Context) error, error) {
	serviceName = name
	exporter := strings.ToLower(os.Getenv(ExporterEnv))
	var (
		endpoint string
		err      error
		exp      sdktrace.SpanExporter
	)
	switch exporter {
	case "otlp":
		endpoint = os.Getenv(OTLPEndpointEnv)
		if endpoint == "" {
			endpoint = DefaultOTLPEndpoint
		}
		exp, err = otlptracehttp.New(context.Background(), otlptracehttp.WithEndpoint(endpoint), otlptracehttp.WithInsecure())
	default:
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

	Logger.SetFormatter(&traceFormatter{})
	Logger.SetOutput(os.Stdout)

	return tp.Shutdown, nil
}
