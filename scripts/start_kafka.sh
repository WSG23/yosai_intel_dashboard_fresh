#!/usr/bin/env bash
# Start the Kafka compose stack and deploy the CDC connector.
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"
COMPOSE_FILE="${COMPOSE_FILE:-docker-compose.kafka.yml}"
CONNECTOR_CONFIG="${1:-${CONNECTOR_CONFIG:-}}"

# Start compose stack
echo "🚀 Starting Kafka stack using $COMPOSE_FILE"
docker compose -f "$ROOT_DIR/$COMPOSE_FILE" up -d

# Wait until containers are ready
"$SCRIPT_DIR/check_kafka_health.sh"

# Create topics and register schemas
"$SCRIPT_DIR/create_kafka_topics.sh"

# Deploy CDC connector when a config file is provided
if [ -n "$CONNECTOR_CONFIG" ] && [ -f "$CONNECTOR_CONFIG" ]; then
  echo "📨 Deploying CDC connector"
  curl -s -X POST \
    -H "Content-Type: application/json" \
    --data "@$CONNECTOR_CONFIG" \
    http://localhost:8083/connectors >/dev/null
else
  echo "⚠️  No connector config supplied; skipping deployment"
fi

echo "✅ Kafka stack ready"

