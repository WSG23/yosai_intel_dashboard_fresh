# Service Discovery

Our deployment now uses Consul for runtime service discovery. Applications
resolve service addresses dynamically instead of relying on static hostnames.

## Configuration

* `CONSUL_HOST` and `CONSUL_PORT` environment variables point to the Consul agent.
* `config/service_discovery.py` exposes `resolve_service(name)` which queries the
  Consul catalog and returns a `host:port` string.

## Example

```python
from config.service_discovery import resolve_service

address = resolve_service("event-service")
```

Services such as `EventServiceAdapter` use this helper with a fallback to
`localhost` when Consul is unavailable.
