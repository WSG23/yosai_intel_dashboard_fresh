#!/usr/bin/env bash
set -euo pipefail

# Run Go unit, integration, and contract tests with coverage and enforce threshold.
ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR/gateway"

# Ensure gocovmerge is available
if ! command -v gocovmerge > /dev/null 2>&1; then
    echo "Installing gocovmerge..."
    GOCOVMERGE_VERSION="${GOCOVMERGE_VERSION:-b5bfa59ec0adc420475f97f89b58045c721d761c}"
    go install "github.com/wadey/gocovmerge@${GOCOVMERGE_VERSION}"
fi

TMP_DIR=$(mktemp -d)
trap 'rm -rf "$TMP_DIR"' EXIT

# Unit tests
go test ./... -coverprofile "$TMP_DIR/unit.out"

# Integration tests (requires build tag 'integration')
go test -tags=integration ./... -coverprofile "$TMP_DIR/integration.out" || true

# Contract tests (requires build tag 'contract')
go test -tags=contract ./... -coverprofile "$TMP_DIR/contract.out" || true

# Merge coverage profiles
PROFILE="$ROOT_DIR/gateway/coverage.out"
gocovmerge "$TMP_DIR"/*.out > "$PROFILE"

cov=$(go tool cover -func "$PROFILE" | awk '/total:/ {print substr($3,1,length($3)-1)}')
echo "Combined coverage: $cov%"

if (( $(echo "$cov < 80" | bc -l) )); then
    echo "Coverage $cov% is below threshold" >&2
    exit 1
fi
