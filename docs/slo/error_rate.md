# Error Rate SLO

- **Objective:** Error rate below 5% over 5 minutes.
- **Measurement:** `rate(http_requests_total{code=~"5.."}[5m]) / rate(http_requests_total[5m])`
- **Alert:** Trigger if error rate exceeds 5% for 5 minutes.

