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
