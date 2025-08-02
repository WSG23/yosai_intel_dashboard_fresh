# Disaster Recovery

This document outlines backup and restore procedures for critical components of the dashboard deployment.

## Database Backup

Regularly back up all databases:
```bash
kubectl exec -it postgres-0 -- pg_dumpall -U postgres > backup/all.sql
```
Store the dump in a secure, off-cluster location.

## Database Restore

To restore from a backup:
```bash
kubectl cp backup/all.sql postgres-0:/tmp/all.sql
kubectl exec -it postgres-0 -- psql -U postgres -f /tmp/all.sql
```
Verify application connectivity after the restore.

## Configuration Backup

Export Kubernetes manifests and ArgoCD configuration:
```bash
kubectl get apps,cm,secret,deploy,svc -A -o yaml > backup/cluster-config.yaml
argocd app export yosai-dashboard > backup/argocd-app.yaml
```
Keep encrypted copies of these files in version control or secure storage.

## Helm Release Backup

Capture the installed Helm chart values:
```bash
helm get values yosai-dashboard -n default > backup/yosai-values.yaml
```
Retain the chart version information with:
```bash
helm list -n default > backup/helm-releases.txt
```

## Restore Helm Release

Reinstall the chart using the saved values:
```bash
helm upgrade --install yosai-dashboard helm/chart -n default -f backup/yosai-values.yaml
```
Synchronize ArgoCD after restoration:
```bash
argocd app sync yosai-dashboard
```

