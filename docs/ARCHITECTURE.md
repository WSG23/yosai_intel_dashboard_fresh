# Architecture

The **Yōsai Intel Dashboard** follows a clean architecture pattern
where core domain logic lives under `yosai_intel_dashboard/src/core`
and framework or I/O concerns reside in adapters and services.

## Layers

- **core** – Entities, value objects and cross-cutting utilities.
- **services** – Application services and domain use cases.
- **pages** – Dash entry points exposing `register_callbacks(app, **deps)`.

Dependencies point inwards to keep business logic isolated and testable.
