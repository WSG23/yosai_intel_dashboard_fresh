#!/usr/bin/env bash
# Development helper utilities for the Yōsai Intel Dashboard.
#
# Usage: ./scripts/dev-helpers.sh {ports|logs|health|load}

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"
# shellcheck source=../common.sh
source "${ROOT_DIR}/common.sh"
COMPOSE_FILE="${COMPOSE_FILE:-docker-compose.yml}"

port_forward() {
  local service="${1:-app}"
  local local_port="${2:-8050}"
  local remote_port="${3:-$local_port}"
  echo "⏩ Port-forwarding $service:$remote_port -> localhost:$local_port"
  if command -v kubectl >/dev/null 2>&1; then
    kubectl port-forward "service/$service" "$local_port:$remote_port"
  else
    echo "kubectl not found; attempting docker compose port" >&2
    docker compose -f "$ROOT_DIR/$COMPOSE_FILE" port "$service" "$remote_port" || return 1
  fi
}

tail_logs() {
  local service="${1:-app}"
  echo "📜 Tailing logs for $service"
  if command -v kubectl >/dev/null 2>&1; then
    kubectl logs -f "deployment/$service"
  else
    docker compose -f "$ROOT_DIR/$COMPOSE_FILE" logs -f "$service"
  fi
}

check_health() {
  local endpoints=("$@")
  if [ ${#endpoints[@]} -eq 0 ]; then
    endpoints=(
      "http://localhost:8050/api/v1/analytics/health"
      "http://localhost:8050/api/v1/compliance/health"
    )
  fi
  local all_ok=0
  for url in "${endpoints[@]}"; do
    echo "Checking $url ..."
    if curl_with_timeout "$url" >/dev/null; then
      echo "✅ $url healthy"
    else
      echo "❌ $url failed"
      all_ok=1
    fi
  done
  return $all_ok
}

run_load_test() {
  local url="${1:-http://localhost:8050/api/v1/analytics/health}"
  local total="${2:-100}"
  local concurrent="${3:-10}"
  echo "🏋️  Running load test: $total requests to $url (concurrency $concurrent)"
  if command -v hey >/dev/null 2>&1; then
    hey -n "$total" -c "$concurrent" "$url"
  else
    echo "hey not installed, using curl loop" >&2
    for ((i=1;i<=total;i++)); do
      curl_with_timeout "$url" >/dev/null &
      ((i % concurrent == 0)) && wait
    done
    wait
    echo "Completed $total requests"
  fi
}

case "${1:-}" in
  ports)
    shift
    port_forward "$@"
    ;;
  logs)
    shift
    tail_logs "$@"
    ;;
  health)
    shift
    check_health "$@"
    ;;
  load)
    shift
    run_load_test "$@"
    ;;
  *)
    echo "Usage: $0 {ports|logs|health|load}" >&2
    exit 1
    ;;
esac
