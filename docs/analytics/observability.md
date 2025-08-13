# Analytics Service Observability

The analytics service emits OpenTelemetry spans for critical operations such as
fetching data from the database and running model inference.  These spans are
exported to the tracing backend configured via `config/telemetry.py`.

To enable tracing, call `configure_tracing()` with the service name and ensure
the environment variables for the Jaeger or Zipkin endpoint are set.  After
starting the service, the spans appear in the configured tracing UI where they
can be inspected for latency and error analysis.
