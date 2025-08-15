# Deployment Cutover and Rollback

## Cutover

1. Set `DEPLOY_ENV` and `TRAFFIC_PERCENT` in the pipeline variables.
2. Run the `canary` stage to deploy the new version to the target environment.
3. Invoke the `traffic_shaping` stage to direct a percentage of traffic using `deployment/scripts/traffic_shaping.sh`.
4. Execute `verify_stateful` to ensure stateful services support simultaneous versions via `deployment/scripts/verify_stateful.sh`.
5. Once checks pass, run the `blue_green` stage to route all traffic to the new release.

## Rollback

1. Run `deployment/scripts/rollback.sh` to revert the deployment.
2. If traffic shaping was applied, set `TRAFFIC_PERCENT=0` and rerun `deployment/scripts/traffic_shaping.sh` to shift all traffic back.
3. Confirm services recover before attempting another deployment.
