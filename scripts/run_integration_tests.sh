#!/usr/bin/env bash
set -euo pipefail

COMPOSE_FILE=${COMPOSE_FILE:-docker-compose.integration.yml}

docker compose -f "$COMPOSE_FILE" up -d --build

cleanup() {
  docker compose -f "$COMPOSE_FILE" down
}
trap cleanup EXIT

pytest integration_tests
