# Feature Flag Management

The dashboard can toggle experimental services on and off at runtime. A
small manager watches a JSON file, Redis instance or remote HTTP
endpoint and exposes the current flag values to the application. Each
flag has a **fallback** value used when dependencies cannot be resolved
or the remote store is unavailable.

## Configuring the Source

Set the `FEATURE_FLAG_SOURCE` environment variable to either a file path
or an HTTP(S) URL that returns a JSON object. If unset, the manager
looks for `feature_flags.json` in the working directory. Alternatively,
configure `FEATURE_FLAG_REDIS_URL` to load flags from Redis (key
`feature_flags`).

```bash
# Local file
export FEATURE_FLAG_SOURCE=/etc/yosai/flags.json

# Remote service
export FEATURE_FLAG_SOURCE=https://config.example.com/flags
```

The file/endpoint/Redis value should return flag definitions. Each
definition may specify the current `enabled` value, a `fallback` value
and optional dependencies:

```json
{
  "use_timescaledb": {"enabled": true, "fallback": false},
  "use_kafka_events": {"enabled": false, "fallback": false},
  "use_analytics_microservice": {"enabled": true, "fallback": false}
}
```

Changes are detected automatically and any registered callbacks are
invoked so services can hot‑reload their configuration. The last
evaluated flag set is persisted to `feature_flags_cache.json` and loaded
on startup before contacting Redis or other sources. If the remote store
is unreachable the cached values are used and a warning is logged.

## Querying Flags

Use `services.feature_flags.feature_flags.is_enabled(name)` to check a
flag:

```python
from yosai_intel_dashboard.src.services.feature_flags import feature_flags

if feature_flags.is_enabled("use_timescaledb"):
    ...
```

Callbacks can be registered with `register_callback` to respond to
updates.

## Managing Flags via API

Administrative clients may modify flags through HTTP endpoints. These
operations require the `feature_admin` role, which must be supplied via
the `X-Roles` header.

```
GET    /api/v1/flags             # list all flags
GET    /api/v1/flags/<name>      # retrieve a single flag
PUT    /api/v1/flags/<name>      # create or update a flag
DELETE /api/v1/flags/<name>      # remove a flag
```

Only users with the `feature_admin` role can call these endpoints.

