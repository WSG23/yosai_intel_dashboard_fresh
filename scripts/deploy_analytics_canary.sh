#!/usr/bin/env bash
set -euo pipefail

kubectl apply -f k8s/canary/analytics-deployment.yaml
kubectl rollout status deployment/analytics-service-canary

