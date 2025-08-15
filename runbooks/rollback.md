# Rollback Runbook

This document describes how to trigger rollbacks for deployments.

## Automated rollback

The deployment pipeline records the current image tag and migration level after
each deployment and uploads them as the `rollback-state` artifact. If the
deployment job fails, a dedicated rollback stage downloads this artifact and
invokes `deployment/scripts/rollback.sh`. No manual intervention is required.

## Manual rollback

A manual rollback can be triggered from the CI interface via the **Rollback**
workflow, which consumes the latest `rollback-state` artifact. You may also run
the script locally:

```bash
bash deployment/scripts/rollback.sh
```

Before running the script manually, ensure that `deployment/rollback_state.json`
contains the desired image tag and migration state.
