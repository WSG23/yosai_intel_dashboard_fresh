#!/usr/bin/env bash
set -euo pipefail
# Create Kafka topics required by the Y\xC5\x8Dsai Intel Dashboard.
# Usage: ./scripts/create_kafka_topics.sh [broker-list]
# Requires kafka-topics.sh from Kafka distribution in your PATH.


BROKERS=${1:-localhost:9092}
# URL of the schema registry used for Avro schemas
SCHEMA_REGISTRY_URL=${SCHEMA_REGISTRY_URL:-http://localhost:8081}

# Default topic configuration values
DEFAULT_SEGMENT_MS=${SEGMENT_MS:-604800000}
DEFAULT_MAX_MESSAGE_BYTES=${MAX_MESSAGE_BYTES:-1048576}
DEFAULT_COMPRESSION_TYPE=${COMPRESSION_TYPE:-gzip}

create_topic() {
  local name=$1
  local partitions=$2
  local retention=$3
  local segment_ms=${4:-$DEFAULT_SEGMENT_MS}
  local max_bytes=${5:-$DEFAULT_MAX_MESSAGE_BYTES}
  local compression=${6:-$DEFAULT_COMPRESSION_TYPE}
  local cleanup=${7:-}
  echo "Creating topic $name"
  kafka-topics.sh \
    --bootstrap-server "$BROKERS" \
    --create \
    --if-not-exists \
    --topic "$name" \
    --partitions "$partitions" \
    --replication-factor 3 \
    --config min.insync.replicas=2 \
    --config segment.ms="$segment_ms" \
    --config retention.ms="$retention" \
    --config max.message.bytes="$max_bytes" \
    --config compression.type="$compression" \
    ${cleanup:+--config cleanup.policy=$cleanup}
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

# Alerts, one week retention
create_topic alerts 3 $((7 * 24 * 60 * 60 * 1000))

# System metrics, one week retention
create_topic system-metrics 3 $((7 * 24 * 60 * 60 * 1000))

# Dead letter queue, one month retention
create_topic dead-letter 3 $((30 * 24 * 60 * 60 * 1000))

# Compacted application state topic
create_topic app-state 3 $((365 * 24 * 60 * 60 * 1000)) $DEFAULT_SEGMENT_MS $DEFAULT_MAX_MESSAGE_BYTES $DEFAULT_COMPRESSION_TYPE compact

# Audit logs, one month retention
create_topic audit-logs 1 $((30 * 24 * 60 * 60 * 1000))

# Register schemas
register_schema schemas/avro/access_event_v1.avsc access-events-value
register_schema schemas/avro/access_event_v1.avsc access-events-enriched-value
register_schema schemas/avro/analytics_event_v1.avsc analytics-events-value
register_schema schemas/avro/anomaly_event_v1.avsc anomaly-events-value
