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

## REST API

Feature flags can also be managed via the dashboard's REST API.

List all flags:

```bash
curl -H "X-Roles: user" http://localhost:8000/v1/feature-flags
```

Retrieve a single flag:

```bash
curl -H "X-Roles: user" http://localhost:8000/v1/feature-flags/use_timescaledb
```

Create or update a flag (requires the `admin` role):

```bash
curl -X POST -H "X-Roles: admin" -H "Content-Type: application/json" \
  -d '{"name": "new_feature", "enabled": true}' \
  http://localhost:8000/v1/feature-flags
```

Delete a flag:

```bash
curl -X DELETE -H "X-Roles: admin" \
  http://localhost:8000/v1/feature-flags/new_feature
```

## CLI Usage

The repository provides a small CLI for interacting with the feature
flag API:

```bash
python cli/feature_flags.py list --roles user
python cli/feature_flags.py create my_flag --enabled --roles admin
python cli/feature_flags.py delete my_flag --roles admin
```
