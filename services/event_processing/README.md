# Event Processing Service

This service consumes events from Kafka, processes them idempotently and exposes Prometheus metrics.

## Configuration

Configuration is loaded from `config/event_processing.yaml` by default. The following environment variables can override values:

- `BROKERS` – comma separated list of Kafka brokers (default `localhost:9092`)
- `GROUP_ID` – consumer group id used for scaling (default `event-processing`)
- `TOPIC` – Kafka topic to consume (default `events`)

The service also loads base options defined in `config/service.yaml` for logging and tracing via the shared framework.

## Building

```
docker build -t event-processing -f services/event_processing/Dockerfile .
```

## Running

```
docker run --rm -e BROKERS=localhost:9092 event-processing
```
