# Microservices Decomposition Plan

This document summarizes the initial planning work for splitting the monolithic
application into smaller services.

## Service Boundary Identification

The `MicroservicesArchitect` inspects modules under the `services/` package and
groups them by common keywords. The default heuristics yield the following
boundaries when run against the repository:

| Boundary            | Modules (excerpt)                                     |
| ------------------- | ----------------------------------------------------- |
| Core Service        | `ai_device_generator`, `task_queue`, `utils`, ...     |
| Analytics Service   | `analytics`, `analytics_service`, `db_analytics_helper` |
| Upload Service      | `upload`, `upload_processing`                          |
| Security Service    | `security`                                            |
| Streaming Service   | `streaming`, `event_streaming_service`                |
| Learning Service    | `learning`, `consolidated_learning_service`           |

These groupings provide a realistic starting point for defining microservice
responsibilities.

## Decomposition Roadmap

After boundaries are identified the next phase is **decomposition**. The
generated roadmap outlines a four phase approach:

1. **Assessment** – enumerate existing modules and categorise them by
   responsibility.
2. **Design** – define APIs and data contracts for each boundary.
3. **Extraction** – split services into independent deployments.
4. **Deployment** – roll out services incrementally while monitoring
   integration points.

## Database Migration for Services

As services split out of the monolith each one now connects to its own
database. The production configuration exposes new environment variables for
these names:

```bash
DB_GATEWAY_NAME=yosai_gateway_db
DB_EVENTS_NAME=yosai_events_db
```

During migration set these variables for each service and run the schema
migrations against the corresponding database. Existing deployments using
`DB_NAME` continue to work, allowing an incremental rollout.

## Service Discovery

Microservices register themselves with a central discovery backend such as
Consul.  The application uses a lightweight client to resolve the network
address for a service at runtime instead of relying on static environment
variables.  The registry endpoint is configured via `SERVICE_REGISTRY_URL`
(defaults to `http://localhost:8500`).  When the analytics or events services
are available in the registry, the application automatically routes requests to
them through the corresponding adapters.
For Kubernetes deployments, DNS resolution is recommended and a registry
client is typically unnecessary.

### Migration to Kubernetes DNS

The preferred setup relies on Kubernetes DNS rather than a registry client.
Services are addressed directly using the pattern
`<service>.<namespace>.svc.cluster.local`.
The legacy `SERVICE_DISCOVERY_URL` variable has been replaced by
`SERVICE_REGISTRY_URL` for local deployments and can be removed from
Kubernetes manifests.

