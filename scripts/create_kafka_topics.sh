#!/usr/bin/env bash
# Create Kafka topics required by the Y\xC5\x8Dsai Intel Dashboard.
# Usage: ./scripts/create_kafka_topics.sh [broker-list]
# Requires kafka-topics.sh from Kafka distribution in your PATH.

set -euo pipefail

BROKERS=${1:-localhost:9092}
# URL of the schema registry used for Avro schemas
SCHEMA_REGISTRY_URL=${SCHEMA_REGISTRY_URL:-http://localhost:8081}

create_topic() {
  local name=$1
  local partitions=$2
  local retention=$3
  echo "Creating topic $name"
  kafka-topics.sh \
    --bootstrap-server "$BROKERS" \
    --create \
    --if-not-exists \
    --topic "$name" \
    --partitions "$partitions" \
    --replication-factor 1 \
    --config retention.ms="$retention"
}

# Register an Avro schema with the schema registry
register_schema() {
  local file=$1
  local subject=$2
  echo "Registering schema $file for subject $subject"
  curl -s -X POST \
    -H "Content-Type: application/vnd.schemaregistry.v1+json" \
    --data "@$file" \
    "$SCHEMA_REGISTRY_URL/subjects/$subject/versions" > /dev/null
}

# Access control events, one week retention
create_topic access-events 3 $((7 * 24 * 60 * 60 * 1000))

# Enriched access events, one month retention
create_topic access-events-enriched 3 $((30 * 24 * 60 * 60 * 1000))

# Detected anomalies, one month retention
create_topic anomaly-events 3 $((30 * 24 * 60 * 60 * 1000))

# Analytics request queue, one week retention
create_topic analytics-requests 3 $((7 * 24 * 60 * 60 * 1000))

# Analytics results, one month retention
create_topic analytics-responses 3 $((30 * 24 * 60 * 60 * 1000))

# Audit logs, one month retention
create_topic audit-logs 1 $((30 * 24 * 60 * 60 * 1000))

# Register schemas
register_schema schemas/access-event.avsc access-events-value
register_schema schemas/access-event.avsc access-events-enriched-value
