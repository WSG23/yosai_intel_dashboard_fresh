#!/usr/bin/env bash
set -euo pipefail

SPEC=${1:-docs/openapi.json}

npx openapi-generator-cli generate -i "$SPEC" -g go -o pkg/eventclient --package-name eventclient >/dev/null 2>&1
npx openapi-generator-cli generate -i "$SPEC" -g python -o analytics/clients/event_client >/dev/null 2>&1
