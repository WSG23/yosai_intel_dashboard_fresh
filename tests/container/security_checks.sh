#!/usr/bin/env bash
set -euo pipefail

IMAGE="${1:-}"
if [[ -z "$IMAGE" ]]; then
  echo "Usage: $0 <docker-image>" >&2
  exit 1
fi

# 1. Confirm container runs as UID 1000
CONTAINER_UID=$(docker run --rm "$IMAGE" id -u)
if [[ "$CONTAINER_UID" != "1000" ]]; then
  echo "Container UID is $CONTAINER_UID but expected 1000" >&2
  exit 1
fi

echo "UID check passed"

# 2. Check for unexpected writable directories
WRITABLE=$(docker run --rm "$IMAGE" sh -c "find / -xdev -type d -writable 2>/dev/null")
if [[ -n "$WRITABLE" ]]; then
  echo "Writable directories:\n$WRITABLE"
fi
# Fail if any writable directories besides /tmp or /var/tmp are present
BAD=$(docker run --rm "$IMAGE" sh -c "find / -xdev -type d -writable ! -path '/tmp' ! -path '/var/tmp' 2>/dev/null")
if [[ -n "$BAD" ]]; then
  echo "Unexpected writable directories found:\n$BAD" >&2
  exit 1
fi

echo "Writable directory check passed"

# 3. Inspect image layers for secrets
if docker history --no-trunc "$IMAGE" | grep -iE 'secret|password|token|key'; then
  echo "Potential secrets found in image history" >&2
  exit 1
fi

echo "No secrets detected in image layers"
