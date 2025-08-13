#!/usr/bin/env bash
set -euo pipefail

COLOR="${1:-green}"

kubectl apply -f "k8s/bluegreen/analytics-${COLOR}.yaml"
kubectl rollout status "deployment/analytics-service-${COLOR}"
kubectl patch service analytics-service -p "{\"spec\":{\"selector\":{\"app\":\"analytics-service\",\"color\":\"${COLOR}\"}}}"

