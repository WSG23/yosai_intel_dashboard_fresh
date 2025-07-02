# Additional Architecture Diagrams

These diagrams complement `architecture.md` by illustrating component interactions and a typical data flow.

## Component Interaction

```mermaid
graph TD
    UI[Browser UI] --> D(Dash frontend)
    D --> F(Flask backend)
    F --> S(Service layer)
    S --> M(Data models)
    M --> DB[(Database)]
```

## Upload Processing Sequence

```mermaid
sequenceDiagram
    participant U as User
    participant FE as Dash frontend
    participant BE as Flask backend
    participant S as Service layer
    participant DB as Database

    U->>FE: Upload file
    FE->>BE: POST /upload
    BE->>S: Validate and parse
    S->>DB: Store records
    S-->>BE: Processed analytics
    BE-->>FE: Return results
    FE-->>U: Show analytics
```
