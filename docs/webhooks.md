# Webhook Alerts

The monitoring utilities send alert messages via a generic webhook when
`AlertConfig.webhook_url` is configured. The payload structure is
simple and mirrors the implementation in
`core/monitoring/user_experience_metrics.py`.

## Payload Schema

```json
{
  "type": "object",
  "properties": {
    "message": {"type": "string"}
  },
  "required": ["message"]
}
```

Example payload:

```json
{
  "message": "High error rate detected"
}
```
