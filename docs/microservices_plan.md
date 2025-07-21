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

