# Chaos Experiments

This directory describes the chaos experiments used in the staging environment.

## Experiments

### Service Kill
- **Manifest**: `deploy/chaos/service-kill.yaml`
- Deletes pods for the `dashboard` application to validate self-healing.
- Injects failures every 10 seconds for one minute.

### Latency Injection
- **Manifest**: `deploy/chaos/latency-injection.yaml`
- Adds 200ms network delay to the `dashboard` pods.
- Helps verify user-facing latency SLOs during network degradation.

## Running

Apply the experiments with:

```bash
python scripts/run_litmus_chaos.py
```

## Rollback

To remove active experiments and restore normal service operation:

```bash
kubectl delete -f deploy/chaos/service-kill.yaml
kubectl delete -f deploy/chaos/latency-injection.yaml
```

## Metrics

After the experiments, capture resilience metrics and push them to the SLO dashboards:

```bash
echo '{"name":"service-kill","duration":60,"succeeded":true}' | \
  python scripts/publish_chaos_metrics.py
```

These metrics populate the resilience panels in the existing SLO dashboards.

## Chaos Mesh

Chaos Mesh provides an alternative framework for fault injection in the staging cluster.

### Installation

Install the operator:

```bash
helm repo add chaos-mesh https://charts.chaos-mesh.org
helm install chaos-mesh chaos-mesh/chaos-mesh -n chaos-testing --create-namespace \
  --set chaosDaemon.runtime=containerd --set chaosDaemon.socketPath=/var/run/containerd/containerd.sock
```

### Experiments

- **Pod Kill** – `deploy/chaos-mesh/pod-kill.yaml` randomly kills a dashboard pod for 30s.
- **Network Delay** – `deploy/chaos-mesh/network-delay.yaml` injects 200ms latency for 1 minute.
- **Network Loss** – `deploy/chaos-mesh/network-loss.yaml` drops all packets for 1 minute.

Apply an experiment with:

```bash
kubectl apply -f deploy/chaos-mesh/<experiment>.yaml
```

Remove with `kubectl delete -f` to stop the fault injection.

### Monitoring and Documentation

While experiments run, watch SLO dashboards to confirm services recover automatically.
Record time-to-recovery and notable alerts in the runbook, then publish metrics:

```bash
echo '{"name":"pod-kill","duration":30,"succeeded":true}' | \\
  python scripts/publish_chaos_metrics.py
```

These steps document resilience and feed recovery data back into the system.
