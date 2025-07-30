# High Level Design

The dashboard follows a modular, service‑oriented architecture built around a
`ServiceContainer`. Each page composes small services obtained from the
container to keep dependencies loosely coupled.  Background workers, the API
gateway and the UI all share the same contracts defined under
`services/interfaces.py`.

```
request -> gateway -> service container -> service -> repository -> database
```

The core layers include:

- **Service Container** – Registers implementations and injects them on demand.
- **Services** – Encapsulate business logic and orchestrate repositories.
- **Repositories** – Handle persistence and external APIs.
- **Plugins** – Optional extensions discovered at runtime.

This layout allows tests to swap in lightweight mocks for any dependency. The
same container setup is reused by the CLI tools and unit tests so behaviour is
consistent across environments.

See `docs/architecture.md` for a detailed breakdown and diagrams of individual
components.
