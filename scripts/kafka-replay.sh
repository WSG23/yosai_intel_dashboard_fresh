#!/usr/bin/env bash
# Replay messages from a source Kafka topic to a target topic.
# Usage: scripts/kafka-replay.sh <source-topic> <target-topic> [broker-list]
# Example: scripts/kafka-replay.sh dead-letter access-events localhost:9092

set -euo pipefail
IFS=$'\n\t'

SOURCE="${1:-}"
TARGET="${2:-}"
BROKERS="${3:-localhost:9092}"

if [[ -z "${SOURCE}" || -z "${TARGET}" ]]; then
  echo "Usage: $0 <source-topic> <target-topic> [broker-list]" >&2
  exit 1
fi

kafka-console-consumer \
  --bootstrap-server "${BROKERS}" \
  --topic "${SOURCE}" \
  --from-beginning \
  --timeout-ms 1000 |
  kafka-console-producer \
  --bootstrap-server "${BROKERS}" \
  --topic "${TARGET}"

echo "Replayed messages from ${SOURCE} to ${TARGET}"
