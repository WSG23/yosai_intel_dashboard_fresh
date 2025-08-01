# Repository Restructure Overview

The monolithic `yosai_intel_dashboard_fresh` repository contains
multiple components written in Python, Go and TypeScript. As the
project matures these components will be split into dedicated
repositories to simplify development and deployment.

## Directories to Extract

- **gateway/** → `yosai-gateway`
  - Go based API gateway and reverse proxy.
- **ui/** → `yosai-dashboard-ui`
  - React front end for the dashboard.
- **yosai-upload/** → `yosai-upload-ui`
  - Standalone upload interface written in React/TypeScript.
- **plugins/** → `yosai-plugins`
  - Collection of first‑party plugins and plugin manager helpers.
- **services/analytics_microservice/** → `analytics-service`
  - Independent analytics engine with TimescaleDB integration.
- **services/security/** → `security-service`
  - Security and authentication logic for downstream services.
- **services/streaming/** → `streaming-service`
  - Kafka and websocket streaming handlers.
- **services/learning/** → `learning-service`
  - Consolidated device learning utilities and models.
- **helm/** and **k8s/** → `yosai-infrastructure`
  - Helm charts and Kubernetes manifests.

These directories will be removed from the main repo once their new
repositories are published.

## Clean Architecture Migration Status

The `scripts/migrate_to_clean_arch.py` helper moves legacy modules into the
`yosai_intel_dashboard/src` hierarchy. Run it with `--report` to view progress.

| Directory | Destination | Status |
|-----------|-------------|--------|
| `core/` | `models` | Completed |
| `models/` | `models` | Completed |
| `services/` | `services` | Completed |
| `config/` | `config` | Completed |
| `monitoring/` | `monitoring` | Completed |
| `security/` | `security` | Completed |
| `api/` | `api` | Completed |
| `plugins/` | `api/plugins` | Completed |

_Migrated 8 of 8 directories (100%)_


## Migration Steps

1. Create new repositories under the organization for each directory
   listed above.
2. Use `git filter-repo` or `git subtree split` to preserve history for
   the extracted paths.
3. Update import paths and package metadata in the new repositories.
4. Update CI/CD pipelines to build and deploy the individual services
   and front ends.
5. Add the new repositories as git submodules or package dependencies
   in this repo until the migration is complete.
6. Remove the directories from the monorepo after successful builds
   and deployment testing.

### Completing Directory Extraction

To move the remaining directories into the clean architecture layout:

1. Ensure your working tree has no uncommitted changes.
2. Optionally create a backup archive:
   ```bash
   python scripts/migrate_to_clean_arch.py --backup migrate_backup.tar.gz
   ```
3. Run the migration script:
   ```bash
   python scripts/migrate_to_clean_arch.py
   ```
4. Verify progress with:
   ```bash
   python scripts/migrate_to_clean_arch.py --report
   ```
5. Commit and push the changes once the report shows 100% migrated.

