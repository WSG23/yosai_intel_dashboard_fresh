# Deployment Diagram

This diagram illustrates how the dashboard container interacts with its database and external services.

```mermaid
flowchart TD
    Browser((User Browser)) -->|HTTPS| Dashboard["Dashboard Container"]
    Dashboard --> Postgres[(PostgreSQL Database)]
    Postgres --> Replicator["Replication Job"]
    Replicator --> Timescale[(TimescaleDB)]
    Dashboard --> Auth0["Auth0 OIDC"]
    Dashboard --> ThreatIntel["Threat Intelligence API"]
    Dashboard --> GeoAPI["Geolocation API"]
```

The migration layer uses **Alembic** to manage schema changes. A lightweight replication job keeps the TimescaleDB instance in sync by polling PostgreSQL for new events.
