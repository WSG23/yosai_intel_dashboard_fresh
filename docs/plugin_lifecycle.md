# Plugin Lifecycle Diagram

```mermaid
graph TB
    A[Discover Plugins] --> B[Resolve Dependencies]
    B --> C[load()]
    C --> D[configure()]
    D --> E[start()]
    E --> F[Plugin Running]
    F --> G[periodic health_check()]
    G --> F
```
