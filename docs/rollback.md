# Kubernetes Rollback Procedure

This project uses a blue/green deployment strategy so that old and new versions can run at the same time. The `yosai-dashboard` service routes traffic to pods labeled with a `color` selector.

1. Deploy the new version using the *green* deployment (`k8s/bluegreen/dashboard-green.yaml`).
2. Verify the new pods are healthy.
3. Switch the service selector from blue to green:
   ```bash
   ./scripts/rollback.sh
   ```
4. Monitor the deployment. If problems occur, run the script again to switch back to the previous color.

The script accepts the service name and namespace as optional arguments:

```bash
./scripts/rollback.sh <service> <namespace>
```

By default it operates on the `yosai-dashboard` service in the `default` namespace.
