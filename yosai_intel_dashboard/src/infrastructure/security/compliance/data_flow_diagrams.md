# Data Flow Diagrams

```mermaid
graph TD
    Client[Client] -->|HTTPS| APIGateway[API Gateway]
    APIGateway --> Services[Internal Services]
    Services --> DB[(Databases)]
    Services --> Analytics[Analytics Pipeline]
```

These diagrams illustrate high-level data movement for compliance audits.
