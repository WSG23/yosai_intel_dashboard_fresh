# Analytics Service Deployment Strategies

This guide explains how to deploy the analytics microservice using blue/green
and canary strategies. Rollback commands are included for each approach.

## Blue/Green

1. Deploy the new color (defaults to `green`):

   ```bash
   ./scripts/deploy_analytics_blue_green.sh green
   ```

2. Monitor the pods until they are ready.

3. If a problem is detected after switching traffic, revert to the previous
   color and remove the failed deployment:

   ```bash
   ./scripts/rollback.sh analytics-service
   kubectl delete -f k8s/bluegreen/analytics-green.yaml
   ```

## Canary

1. Launch a canary alongside the existing deployment:

   ```bash
   ./scripts/deploy_analytics_canary.sh
   ```

2. Validate metrics and logs. The canary receives a small portion of traffic
   because only one replica is created.

3. Roll back by removing the canary deployment:

   ```bash
   kubectl delete deployment analytics-service-canary
   ```

4. To promote the canary, apply the regular production manifests and then
   delete the canary deployment.

