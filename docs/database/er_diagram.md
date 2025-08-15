# Entity Relationship Diagram

Generated automatically from migrations.

```mermaid
erDiagram
    access_events ||--o{ anomaly_detections : ""
    permissions ||--o{ role_permissions : ""
    roles ||--o{ role_permissions : ""
    roles ||--o{ user_roles : ""
```
