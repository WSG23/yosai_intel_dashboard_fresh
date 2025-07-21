#!/usr/bin/env bash
set -euo pipefail

# Install k3s (lightweight Kubernetes)
if ! command -v k3s >/dev/null 2>&1; then
  curl -sfL https://get.k3s.io | sh -
fi

export KUBECONFIG=/etc/rancher/k3s/k3s.yaml

# Install Linkerd CLI if missing
if ! command -v linkerd >/dev/null 2>&1; then
  curl -sL https://run.linkerd.io/install | sh
  export PATH=$PATH:$HOME/.linkerd2/bin
fi

# Install Linkerd control plane and viz extension
linkerd install --crds | kubectl apply -f -
linkerd install | kubectl apply -f -
linkerd viz install | kubectl apply -f -

# Install ingress controller
kubectl apply -f https://raw.githubusercontent.com/kubernetes/ingress-nginx/main/deploy/static/provider/baremetal/deploy.yaml

# Install cert-manager
kubectl apply -f https://github.com/cert-manager/cert-manager/releases/latest/download/cert-manager.yaml

# Install metrics-server
kubectl apply -f https://github.com/kubernetes-sigs/metrics-server/releases/latest/download/components.yaml

# Install Prometheus stack via Helm
if ! command -v helm >/dev/null 2>&1; then
  curl https://raw.githubusercontent.com/helm/helm/master/scripts/get-helm-3 | bash
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
