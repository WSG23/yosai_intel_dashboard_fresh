#!/usr/bin/env bash
# Create Kafka topics required by the Y\xC5\x8Dsai Intel Dashboard.
# Usage: ./scripts/create_kafka_topics.sh [broker-list]
# Requires kafka-topics.sh from Kafka distribution in your PATH.

set -euo pipefail

BROKERS=${1:-localhost:9092}

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

# Access control events, one week retention
create_topic access-events 3 $((7 * 24 * 60 * 60 * 1000))

# Detected anomalies, one month retention
create_topic anomaly-events 3 $((30 * 24 * 60 * 60 * 1000))

# Audit logs, one month retention
create_topic audit-logs 1 $((30 * 24 * 60 * 60 * 1000))
