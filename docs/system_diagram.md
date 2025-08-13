# System Diagram

This document outlines the high-level components of the platform and how they communicate. It serves as an entry point; for a deeper look at the application layering see [Architecture](architecture.md) and for runtime messaging refer to [Data Flow](data_flow.md). The PlantUML source for this diagram is available in [system_diagram.puml](system_diagram.puml).

```plantuml
@startuml
skinparam componentStyle rectangle
actor Browser

package "Frontend" {
  [Web UI] as UI
}

package "Service Layer" {
  [API Gateway] as API
  [Business Services] as Services
  [Plugin Manager] as PluginManager
  [Background Worker] as Worker
}

package "Data Stores" {
  database DB
  queue MQ
}

Browser --> UI
UI --> API
API --> Services
Services --> DB
Services --> MQ
Services --> PluginManager
MQ --> Worker
@enduml
```

The diagram highlights the service boundaries: the Web UI issues HTTP calls to the API gateway, services encapsulate business logic and plugin management, and data persists through the database or flows asynchronously via the message queue to background workers.

For additional context see the [Architecture](architecture.md) and [Data Flow](data_flow.md) documents which provide more detailed design and sequence information.
