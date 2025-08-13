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
