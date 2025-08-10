#!/usr/bin/env bash
set -euo pipefail
# Wait until Kafka docker-compose stack becomes healthy.

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"
COMPOSE_FILE="${COMPOSE_FILE:-docker-compose.kafka.yml}"

SERVICES=(
  zookeeper
  kafka1 kafka2 kafka3
  schema-registry kafka-ui kafka-init
)

MAX_RETRIES=${MAX_RETRIES:-30}
SLEEP_INTERVAL=${SLEEP_INTERVAL:-5}

for ((i=1;i<=MAX_RETRIES;i++)); do
  all_up=true
  for svc in "${SERVICES[@]}"; do
    cid=$(docker compose -f "$ROOT_DIR/$COMPOSE_FILE" ps -q "$svc")
    if [ -z "$cid" ]; then
      all_up=false
      break
    fi
    status=$(docker inspect -f '{{.State.Health.Status}}' "$cid" 2>/dev/null || echo "")
    state=$(docker inspect -f '{{.State.Status}}' "$cid")
    if [[ "$status" == "healthy" || "$state" == "running" ]]; then
      continue
    else
      all_up=false
      break
    fi
  done
  if $all_up; then
    echo "✅ Kafka services healthy"
    exit 0
  fi
  echo "⏳ Waiting for Kafka stack to become healthy ($i/$MAX_RETRIES)"
  sleep "$SLEEP_INTERVAL"
done

echo "❌ Kafka stack did not become healthy in time"
exit 1

