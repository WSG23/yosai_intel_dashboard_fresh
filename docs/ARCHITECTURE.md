# High-Level Architecture

The dashboard follows a microservice style design. A Flask & Dash front end
communicates with several background services using REST and message queues.
A lightweight dependency injection container wires these pieces together and
allows tests to replace implementations easily.

Key elements:

- **Service Container** – central registry that provides shared services and
  resolves dependencies on demand.
- **Plugins** – optional packages discovered at startup to extend the system
  without modifying core modules.
- **Analytics Service** – background worker that performs heavy data processing
  and exposes an async API.
- **Gateway** – small Go proxy that exposes the API to the network and
  orchestrates authentication and rate limiting.

All interactions go through well defined protocols located under
`services/interfaces.py`.  The container provides default implementations but
alternate ones can be registered for testing or custom deployments.

See `docs/architecture.md` and related diagrams for a more detailed breakdown.
