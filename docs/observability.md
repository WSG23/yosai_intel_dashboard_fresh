# Observability

All services expose health and Prometheus metrics endpoints.

## Endpoints

- `GET /health` – basic liveness check returning `{"status":"ok"}`.
- `GET /health/live` – service is running.
- `GET /health/ready` – service is ready to accept traffic.
- `GET /metrics` – Prometheus metrics in the default format.

## Kubernetes Probes

Deployments use HTTP probes against `/health`:

- `readinessProbe` ensures the service is ready.
- `livenessProbe` restarts unhealthy containers.

## Prometheus Scraping

Pods and Services are annotated with:

```
prometheus.io/scrape: "true"
prometheus.io/path: "/metrics"
prometheus.io/port: "<port>"
```

These annotations or accompanying `ServiceMonitor` resources allow Prometheus to
scrape the metrics endpoints automatically.

## Metrics

The platform tracks key decision activity, gateway traffic, and queue processing:

- `service_decisions_total{service,decision}` – counter of important decisions made by each service.
- `service_decision_latency_seconds{service,decision}` – histogram of decision latency in seconds.
- `gateway_http_requests_total{path,method,status}` – number of HTTP requests handled by the gateway.
- `gateway_http_request_duration_seconds{path,method}` – latency of HTTP requests in seconds.
- `queue_processed_messages_total{queue}` – count of messages processed successfully.
- `queue_processing_errors_total{queue}` – count of handler errors while processing messages.

Both the `gateway` and `queue` services expose `/metrics` endpoints for Prometheus scraping.

## SLO Targets

| Metric | Target |
| --- | --- |
| Decision latency p95 | < 0.5s |
| Gateway request latency p95 | < 0.5s |
| Queue processing error rate | < 1% |
| Error budget remaining | ≥ 99.9% |

Dashboards and alerting rules for these SLOs live in `deploy/grafana/`.
