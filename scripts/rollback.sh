#!/usr/bin/env bash
set -euo pipefail

DEPLOYMENT="${1:-api-gateway}"
NAMESPACE="${2:-default}"
PROM_URL="${PROM_URL:-http://prometheus:9090}"

P95_QUERY='histogram_quantile(0.95, sum(rate(unlock_latency_seconds_bucket[5m])) by (le))'
ERROR_QUERY='sum(rate(unlock_errors_total[5m])) / sum(rate(unlock_requests_total[5m]))'

while true; do
  p95=$(curl -s "$PROM_URL/api/v1/query" --data-urlencode "query=$P95_QUERY" | jq -r '.data.result[0].value[1]')
  err=$(curl -s "$PROM_URL/api/v1/query" --data-urlencode "query=$ERROR_QUERY" | jq -r '.data.result[0].value[1]')

  p95_ms=$(awk "BEGIN {print $p95 * 1000}")
  err_pct=$(awk "BEGIN {print $err * 100}")
  echo "p95=${p95_ms}ms error=${err_pct}%"

  p95_bad=$(awk "BEGIN {print ($p95_ms > 100)}")
  err_bad=$(awk "BEGIN {print ($err_pct > 1)}")
  if [[ $p95_bad -eq 1 || $err_bad -eq 1 ]]; then
    echo "SLO breach detected, rolling back $DEPLOYMENT"
    kubectl rollout undo deployment "$DEPLOYMENT" -n "$NAMESPACE"
    exit 0
  fi

  sleep 60
done
