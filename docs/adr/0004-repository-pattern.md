# ADR 0004: Repository Pattern

## Context
Data access logic was scattered across services, coupling business code to specific storage implementations.

## Decision
Apply the Repository pattern to abstract persistence behind interfaces. Concrete repositories implement data access for each entity while clients depend on interfaces.

## Consequences
- Business logic remains storage agnostic.
- Easier to swap or mock data sources in tests.
- Requires extra boilerplate for simple queries.
