# Internal Service Interfaces

This reference summarizes key APIs used by internal services.

## StreamingService

`services/streaming/service.py` manages Kafka or Pulsar connections. The public API consists of:

- `initialize()` – start the service and establish producer/consumer connections based on the configuration.
- `publish(data: bytes, topic: Optional[str] = None)` – send a byte payload to the configured topic.
- `consume(timeout: float = 1.0) -> Generator[bytes, None, None]` – yield messages from the subscribed topic.
- `close()` – cleanly close the producer, consumer and underlying client.

These methods abstract away the differences between Kafka and Pulsar. The service chooses the appropriate client in `initialize()` depending on the `service_type` field in the dynamic configuration.

## Webhook Alert Configuration

`core/monitoring/user_experience_metrics.py` defines an `AlertConfig` dataclass used by `AlertDispatcher`. The configuration fields are:

- `slack_webhook` – Slack incoming webhook URL for chat notifications.
- `email` – address to send email alerts via the local SMTP server.
- `webhook_url` – generic HTTP webhook endpoint receiving JSON payloads.

`AlertDispatcher.send_alert()` checks each field and posts the alert message to the configured destinations.

## WebSocket Message Format

`AnalyticsWebSocketServer` in `services/websocket_server.py` broadcasts analytics events over WebSockets. Each call to `broadcast(data)` converts the dictionary `data` to JSON and sends it to all connected clients. Clients therefore receive messages such as:

```json
{"file": "sample.csv"}
```

Any event payload published to the `EventBus` under the `analytics_update` topic is forwarded in this JSON format.
