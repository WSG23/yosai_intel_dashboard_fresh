# ADR 0002: ConfigService

## Context
Configuration data was previously pulled directly from environment files in multiple modules, making it difficult to reload or validate settings.

## Decision
Create a ConfigService responsible for loading, transforming and providing configuration values through a single interface. Clients depend on the service instead of reading files or environment variables.

## Consequences
- Hot-reloading of configuration becomes feasible.
- Validation is performed in one place.
- Requires wiring the service into the dependency container.
