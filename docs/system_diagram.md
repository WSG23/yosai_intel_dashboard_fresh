# System Flow Diagram

This diagram illustrates how the frontend interacts with the service layer, plugins, and the database.

```mermaid
flowchart TD
    Browser -->|HTTP| UI["Web UI"]
    UI -->|Calls| Services
    Services -->|Queries| DB[(Database)]
    Services --> PluginManager
    PluginManager --> Plugins
    Plugins -->|Register callbacks| UI
```

