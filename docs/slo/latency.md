# Latency SLO

- **Objective:** 95% of requests complete within 500ms.
- **Measurement:** `histogram_quantile(0.95, sum(rate(http_request_duration_seconds_bucket[5m])) by (le))`
- **Alert:** Trigger if latency exceeds 500ms for 5 minutes.

