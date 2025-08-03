# ADR 0003: EventBus

## Context
As features grew, modules needed a way to react to domain events without tight coupling.

## Decision
Adopt a simple in-memory EventBus implementing pub/sub semantics. Publishers emit events by type and subscribers register handlers. See the [event bus diagram](../architecture/event_bus.svg) and [event flow sequence](../architecture/event_processing_sequence.svg) for the final design.

## Consequences
- Components communicate without direct references.
- Historical events can be inspected during debugging.
- In-memory bus does not persist events across process restarts.
