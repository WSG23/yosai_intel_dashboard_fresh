# Feature Flag Management

The dashboard can toggle experimental services on and off at runtime. A
small manager watches a JSON file or remote endpoint and exposes the
current flag values to the application.

## Configuring the Source

Set the `FEATURE_FLAG_SOURCE` environment variable to either a file path
or an HTTP(S) URL that returns a JSON object. If unset, the manager
looks for `feature_flags.json` in the working directory.

```bash
# Local file
export FEATURE_FLAG_SOURCE=/etc/yosai/flags.json

# Remote service
export FEATURE_FLAG_SOURCE=https://config.example.com/flags
```

The file or endpoint should return a simple mapping of flag names to
boolean values:

```json
{
  "use_timescaledb": true,
  "use_kafka_events": false,
  "use_analytics_microservice": true
}
```

Changes are detected automatically and any registered callbacks are
invoked so services can hot‑reload their configuration.

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
