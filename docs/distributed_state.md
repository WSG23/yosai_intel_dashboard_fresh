# Distributed State Management

Yosai deploys analytics, event processing and the API gateway as
independent services.  Kafka, Redis and database replication keep these
components in sync even when updates arrive out of order.

## Event Streaming with Kafka

Each service publishes domain events to Kafka topics.  Consumers update
local caches and write to their databases asynchronously.  Because
producers never block on consumers, messages may be processed later but
no data is lost.  Lagging consumers eventually catch up and converge to
the latest state.

## Caching and Locks in Redis

Redis stores short‑lived data and distributed locks.  The cache is
replicated between instances so that configuration flags, session data
and rate limits are visible across the cluster.  Stale entries expire
quickly, ensuring that all nodes observe the same behaviour within a few
seconds.

## Database Replication

PostgreSQL uses streaming replication for long‑term persistence.  Each
microservice writes to its own database while replicas propagate changes
to standby nodes.  Reads may momentarily return slightly older data but
the replicas eventually apply the same updates.

## Reverting to the Monolith

Set the migration flags to `false` if you need to disable the
microservices and route all requests to the built‑in implementations.
Create a flag file such as `feature_flags.json` with:

```json
{
  "use_analytics_microservice": false,
  "use_kafka_events": false,
  "use_timescaledb": false
}
```

Then point the service at this file:

```bash
export FEATURE_FLAG_SOURCE=/path/to/feature_flags.json
```

Run `./scripts/rollback.sh` to flip the Kubernetes service selector back to
the previous deployment.  The dashboard will then operate as a
self‑contained monolith until the microservices are re‑enabled.
