# Yōsai Intel Helm Charts

This directory contains the Helm charts for deploying the **Yōsai Intel Dashboard**.

## Configuration
Key parameters in `values.yaml`:

| Parameter | Description | Default |
|-----------|-------------|---------|
| `environment` | Environment name (`dev`, `staging`, `prod`) | `dev` |
| `image.repository` | Container image repository | `yosai-intel-dashboard` |
| `image.tag` | Container image tag | `0.1.0` |
| `replicaCount` | Number of pod replicas | `2` |
| `postgresql.enabled` | Deploy Bitnami PostgreSQL chart | `false` |
| `redis.enabled` | Deploy Bitnami Redis chart | `false` |
| `kafka.enabled` | Deploy Bitnami Kafka chart | `false` |
| `migrations.enabled` | Run database migration job on install/upgrade | `true` |

Environment-specific overrides live in `values-<env>.yaml` files.

## Usage
First, pull dependent charts:

```sh
helm dependency update helm/yosai-intel
```

### Development
```sh
helm install yosai-intel helm/yosai-intel -f helm/yosai-intel/values-dev.yaml
```

### Staging
```sh
helm install yosai-intel helm/yosai-intel -f helm/yosai-intel/values-staging.yaml
```

### Production
```sh
helm install yosai-intel helm/yosai-intel -f helm/yosai-intel/values-prod.yaml
```

Upgrades and rollbacks can be managed using standard Helm commands:

```sh
helm upgrade yosai-intel helm/yosai-intel -f helm/yosai-intel/values-prod.yaml
helm rollback yosai-intel <REVISION>
```
