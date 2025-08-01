# Observability Guide

The dashboard ships with a lightweight observability stack for local development.
Structured logs are forwarded by Logstash and traces are exported to Jaeger.

## Service Metadata

The Go tracing helpers under `gateway/internal/tracing` attach service metadata
to every span and log entry. Two environment variables are read at startup:

- `SERVICE_VERSION` – version string for the running service (`0.0.0` by
  default)
- `APP_ENV` – environment name such as `development` or `production`
  (`development` by default)

Example environment file:

```bash
SERVICE_VERSION=1.2.3
APP_ENV=staging
```

With these variables set, a log line looks similar to the following:

```json
{"level":"info","service":"gateway","service_version":"1.2.3","environment":"staging","msg":"starting server","time":"2024-01-01T12:00:00Z","trace_id":"...","span_id":"..."}
```

## Viewing Logs

1. Start the Logstash container:
   ```bash
   docker run -p 5044:5044 \
     -v $(pwd)/logging/logstash.conf:/usr/share/logstash/pipeline/logstash.conf \
     docker.elastic.co/logstash/logstash:8
   ```
2. Point Filebeat or your log shipper to `localhost:5044`. Logs are JSON encoded
   and include `service`, `service_version` and `environment` fields as well as
   trace identifiers when available.
3. If using the provided `docker-compose.dev.yml`, logs can also be viewed in
   Kibana once an Elasticsearch instance is connected.

## Viewing Traces

1. Launch the Jaeger all-in-one image (already included in
   `docker-compose.dev.yml`):
   ```bash
   docker-compose -f docker-compose.dev.yml up jaeger
   ```
2. Open the Jaeger UI at [http://localhost:16686](http://localhost:16686) and
   select the desired service from the dropdown.
3. Spans from all services will appear when the `JAEGER_ENDPOINT` environment
   variable points to the collector (defaults to
   `http://localhost:14268/api/traces`).

This setup lets you correlate logs with traces to debug issues across services.
