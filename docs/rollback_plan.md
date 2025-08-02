# Rollback Plan

## Pre-deployment Checklist

- [ ] Backup current deployment state
- [ ] Document current version/image tag
- [ ] Test rollback procedure in staging
- [ ] Ensure team knows rollback process

## Rollback Triggers

Define when to rollback:

- Import errors > X%
- Health check failures
- Performance degradation > Y%
- Critical functionality broken

## Rollback Procedures

**Level 1: Quick Rollback (< 5 minutes)**

```bash
# Kubernetes deployment rollback
kubectl rollout undo deployment/yosai-dashboard

# Verify
kubectl rollout status deployment/yosai-dashboard
```

**Level 2: Image Rollback (< 15 minutes)**

```bash
# Revert to specific image
kubectl set image deployment/yosai-dashboard \
  yosai-dashboard=ghcr.io/wsg23/yosai-dashboard:<previous-tag>
```

**Level 3: Full Rollback (< 30 minutes)**

- Database migration rollback
- Configuration rollback
- Code revert

## Post-Rollback Actions

- Incident report template
- Communication plan
- Root cause analysis
