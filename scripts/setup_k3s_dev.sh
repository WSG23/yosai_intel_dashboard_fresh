#!/usr/bin/env bash
set -euo pipefail

# shellcheck source=./common.sh
COMMON_SH="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" >/dev/null 2>&1 && pwd)/common.sh"
if [ -f "$COMMON_SH" ]; then . "$COMMON_SH"; else
  echo "Warning: common.sh not found at $COMMON_SH; continuing without it." >&2
fi

# Install k3s (lightweight Kubernetes)
if ! command -v k3s >/dev/null 2>&1; then
  curl_with_timeout --location https://get.k3s.io | sh -
fi

export KUBECONFIG="/etc/rancher/k3s/k3s.yaml"

# Install Istio CLI if missing
if ! command -v istioctl >/dev/null 2>&1; then
  curl_with_timeout --location https://istio.io/downloadIstio | ISTIO_VERSION=1.21.0 sh -
  istio_bin="$(pwd)/istio-1.21.0/bin"
  export PATH="${PATH}:${istio_bin}"
fi

# Install Istio control plane using the demo profile
istioctl install -y --set profile=demo

# Label namespaces for automatic sidecar injection
for ns in yosai-prod yosai-staging yosai-dev; do
  kubectl label namespace "$ns" istio-injection=enabled --overwrite
done

# Install ingress controller
curl_with_timeout --location https://raw.githubusercontent.com/kubernetes/ingress-nginx/main/deploy/static/provider/baremetal/deploy.yaml | kubectl apply -f -

# Install cert-manager
curl_with_timeout --location https://github.com/cert-manager/cert-manager/releases/latest/download/cert-manager.yaml | kubectl apply -f -

# Install metrics-server
curl_with_timeout --location https://github.com/kubernetes-sigs/metrics-server/releases/latest/download/components.yaml | kubectl apply -f -

# Install Prometheus stack via Helm
if ! command -v helm >/dev/null 2>&1; then
  curl_with_timeout --location https://raw.githubusercontent.com/helm/helm/master/scripts/get-helm-3 | bash
fi
helm repo add prometheus-community https://prometheus-community.github.io/helm-charts
helm repo update
helm install monitoring prometheus-community/kube-prometheus-stack \
  --namespace monitoring --create-namespace

# Create application namespaces
for ns in yosai-prod yosai-staging yosai-dev; do
  kubectl create namespace "$ns" --dry-run=client -o yaml | kubectl apply -f -
done

# Apply base manifests
kubectl apply -f k8s/base

# Apply Istio service mesh configuration
kubectl apply -f k8s/istio
