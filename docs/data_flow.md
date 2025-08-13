# Data Flow Overview

For the big-picture service layout, refer to the [System Diagram](system_diagram.md).

```mermaid
sequenceDiagram
    participant Browser
    participant Server
    participant MQ as Kafka/Redis
    participant Worker
    participant DB as Database
    participant EH as ErrorHandler

    Browser->>Server: HTTP request
    Server->>DB: Query / Update
    DB-->>Server: Result
    Server-->>Browser: Rendered response
    Server-->>MQ: Publish event
    MQ-->>Worker: Consume
    Worker-->>Server: Callback result
    Worker->>EH: Error occurred?
    EH-->>Server: Raise or log
```

## Retry Logic and Circuit Breakers

Services publish events using `with_retry` and `CircuitBreaker` from
`core.error_handling`. Retries use exponential backoff and failures increment the
circuit breaker metrics. When a breaker opens, subsequent messages are rejected
and the error handler notifies the caller so issues surface quickly.
