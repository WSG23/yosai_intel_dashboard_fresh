#!/usr/bin/env bash
set -euo pipefail

STATE_FILE="$(dirname "$0")/../rollback_state.json"

if [[ ! -f "$STATE_FILE" ]]; then
  echo "State file $STATE_FILE not found" >&2
  exit 1
fi

IMAGE_TAG=$(jq -r '.image' "$STATE_FILE")
MIGRATION_STATE=$(jq -r '.migration' "$STATE_FILE")

if [[ -z "$IMAGE_TAG" || "$IMAGE_TAG" == "null" ]]; then
  echo "Image tag missing in state file" >&2
  exit 1
fi

if [[ -z "$MIGRATION_STATE" || "$MIGRATION_STATE" == "null" ]]; then
  echo "Migration state missing in state file" >&2
  exit 1
fi

echo "Rolling back container image to $IMAGE_TAG"
# Example rollback command for Kubernetes deployment
kubectl set image deployment/dashboard dashboard="$IMAGE_TAG" --record || true

echo "Reverting database to migration $MIGRATION_STATE"
"$(dirname "$0")/../../migrations/rollback.sh" "$MIGRATION_STATE"

echo "Rollback completed"
