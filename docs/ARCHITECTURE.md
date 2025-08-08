# Architecture

The Yōsai Intel Dashboard follows a clean architecture pattern
where core domain logic lives under yosai_intel_dashboard/src/core
and all framework or I/O concerns reside in adapters and services.

## Layers

- core – Entities, value objects and cross-cutting utilities.
- services – Application services and domain use cases.
- pages – Dash/React entry points. Each page exposes register_callbacks(app, **deps) to wire Dash callbacks.

Dependencies always point inwards; interfaces depend on services which
depend on the core. This keeps business logic testable and isolated.
