# ADR 0006: Deprecation Shims for Renamed APIs

## Context
Several public APIs were relocated or renamed as part of ongoing
refactoring. External integrations still rely on the legacy entry
points.

## Decision
Maintain thin compatibility shims at the old import locations. Each
shim forwards calls to the new implementation and issues a
`DeprecationWarning` to alert downstream users.

## Consequences
- Enables incremental migration for integrators.
- Requires maintaining additional wrapper code until the next major
  release when the shims can be removed.
