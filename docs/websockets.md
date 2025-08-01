# WebSocket Events

`services/websocket_server.py` exposes `AnalyticsWebSocketServer`, a
broadcast-only server that sends analytics updates to all connected
clients. It listens for `analytics_update` events on the internal
`EventBus` and forwards the payload as a JSON message.

Clients connect to `ws://<host>:<port>` (default `0.0.0.0:6789`). The
message format is an arbitrary JSON object describing the analytics
update. A common example is the dashboard summary emitted by
`AnalyticsService.get_dashboard_summary`.

## Message Schema

```json
{
  "type": "object",
  "description": "Analytics update data",
  "additionalProperties": true
}
```

Example message:

```json
{
  "status": "ok",
  "data_summary": {"total_records": 120}
}
```

## Demo Provider

`services/websocket_data_provider.py` offers a small helper that periodically
publishes sample analytics to the `EventBus`. When used together with
`AnalyticsWebSocketServer` it enables a fully self-contained demo of the real
-time dashboard:

```python
from yosai_intel_dashboard.src.core.events import EventBus
from yosai_intel_dashboard.src.services.websocket_server import AnalyticsWebSocketServer
from yosai_intel_dashboard.src.services.websocket_data_provider import WebSocketDataProvider

bus = EventBus()
server = AnalyticsWebSocketServer(bus)
provider = WebSocketDataProvider(bus)
```

The provider runs on a background thread and can be stopped via
`provider.stop()`.
