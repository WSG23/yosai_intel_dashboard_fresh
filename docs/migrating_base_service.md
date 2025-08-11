# Migrating from the old BaseService

The legacy `BaseService` bundled logging, metrics and tracing in a single struct.
New applications should use the `ServiceBuilder` and component interfaces
introduced in `go/framework`.

1. Import the builder and create a new instance:
   ```go
   builder, _ := framework.NewServiceBuilder("service-name", "config.yaml")
   svc, _ := builder.Build()
   ```
2. Start the returned `BaseService` as usual:
   ```go
   go svc.Start()
   defer svc.Stop()
   ```

The builder configures a zap logger, Prometheus metrics collector and Jaeger
tracer. Custom implementations can be supplied via the `WithLogger`,
`WithMetrics` and `WithTracer` methods before calling `Build`.

Configuration is validated against `config/service.schema.yaml` by default.
Set the `YOSAI_SCHEMA_PATH` environment variable to point to a different
schema file when needed.
