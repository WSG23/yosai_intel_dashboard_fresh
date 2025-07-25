# Chaos Testing Setup

This guide explains how to run weekly chaos experiments using [Litmus](https://litmuschaos.io).

## Installation

1. Apply `k8s/chaos/litmus-install.yaml` to install the Litmus operator.
2. Ensure kubectl is configured for the staging cluster.

```bash
kubectl apply -f k8s/chaos/litmus-install.yaml
```

## Experiments

The `k8s/chaos` folder contains example Litmus experiments:

- `network-chaos.yaml` – simulate packet loss
- `resource-stress.yaml` – CPU hog scenario
- `pod-delete.yaml` – delete service pods
- `data-corruption.yaml` – fill disk to test corruption

Apply the experiments using the helper script:

```bash
python scripts/run_litmus_chaos.py
```

## Automated Recovery

Each experiment should verify the service recovers after chaos injection. Configure your monitoring to alert on failed recovery.

## Scheduling

Use the `chaos-tests` GitHub Actions workflow to run the experiments weekly in the staging environment.
