# 1. Introduce Repository Pattern

## Status
Accepted

## Context
Metrics endpoints and WebSocket services previously accessed data directly through module-level structures. This tight coupling made unit testing difficult and obscured persistence boundaries.

## Decision
Define `MetricsRepository` protocol and `InMemoryMetricsRepository` implementation under `src/repository/`. Business services inject the repository interface instead of using hard-coded data. The [repository interface diagram](../architecture/repositories.svg) illustrates how concrete implementations relate to their abstractions.

## Consequences
* Data access can be swapped without changing service logic.
* Unit tests use in-memory repositories for fast, isolated testing.
* Future persistence layers (database, API) can implement the repository protocol.
