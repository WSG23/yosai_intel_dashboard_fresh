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
