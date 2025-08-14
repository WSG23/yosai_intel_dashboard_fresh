# Rollback Runbook

This document describes how to trigger rollbacks for deployments.

## Automated rollback

The deployment pipeline includes a rollback stage that executes automatically
when a deployment job fails. The stage invokes `deployment/scripts/rollback.sh`
using the last-known-good image tag and migration state stored in
`deployment/rollback_state.json`.

## Manual rollback

A manual rollback can be triggered from the CI interface via the `Rollback`
workflow. You may also run the script locally:

```bash
bash deployment/scripts/rollback.sh
```

Ensure that `deployment/rollback_state.json` contains the desired target before
running the script.
