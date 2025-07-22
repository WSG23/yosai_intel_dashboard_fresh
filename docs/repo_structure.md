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

