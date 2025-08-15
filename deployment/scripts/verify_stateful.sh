#!/bin/bash
set -euo pipefail

ENV=${DEPLOY_ENV:-staging}
SERVICE_LABEL=${1:-dashboard-db}

VERSIONS=$(kubectl --context "$ENV" get pods -l app="$SERVICE_LABEL" -o jsonpath='{.items[*].metadata.labels.version}' | tr ' ' '\n' | sort -u | wc -l)
if [ "$VERSIONS" -lt 2 ]; then
  echo "Stateful service $SERVICE_LABEL does not handle simultaneous versions"
  exit 1
fi

echo "Stateful service $SERVICE_LABEL handles simultaneous versions"
