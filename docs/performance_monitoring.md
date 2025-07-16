# Performance Monitoring

The dashboard collects runtime metrics through the `core.performance` module. A global
`PerformanceMonitor` instance records execution times, memory usage and CPU load.
Use `get_performance_monitor()` to access it and view summaries.

```python
from core.performance import get_performance_monitor
summary = get_performance_monitor().get_metrics_summary()
```

Snapshots are taken automatically in the background and can be visualized or exported
for further analysis.


## External Metrics Collection

Prometheus and Logstash can aggregate metrics and logs from all containers.

### Prometheus

The sample configuration `monitoring/prometheus.yml` scrapes metrics from the
application itself, a PostgreSQL exporter and a Redis exporter. Launch it with:

```bash
docker run -p 9090:9090 \
  -v $(pwd)/monitoring/prometheus.yml:/etc/prometheus/prometheus.yml \
  prom/prometheus
```

### Logstash

`logging/logstash.conf` reads the application, Postgres and Redis logs and can
forward them to Elasticsearch. Start a Logstash container with:

```bash
docker run -p 5044:5044 \
  -v $(pwd)/logging/logstash.conf:/usr/share/logstash/pipeline/logstash.conf \
  docker.elastic.co/logstash/logstash:8
```

Adjust the `elasticsearch` output section if you have a different destination.


## Real-time Performance Tracking

The `core.monitoring.real_time_performance_tracker` module captures Core Web Vitals
and server side metrics such as upload speed and callback duration. Metrics are
stored using the existing `PerformanceMonitor` instance.

Enable default thresholds in `config/monitoring.yaml` and adjust the Slack or
email settings to receive alerts.

A basic dashboard is available in `dashboards/performance/` for quick visual
checks of recent activity.

### UI Monitoring

Client side frame times and callback runtimes can be captured using
`monitoring.ui_monitor.RealTimeUIMonitor`. The metrics are forwarded to the
shared `PerformanceMonitor` instance.

```python
from monitoring.ui_monitor import get_ui_monitor

ui = get_ui_monitor()
ui.record_frame_time(16.7)
ui.record_callback_duration("update_chart", 0.05)
```

## Caching Strategy

Several analytics methods use `advanced_cache.cache_with_lock` to store results.
The decorator prevents concurrent execution of expensive operations by locking
per function and caches the return value for a configurable TTL.

For example, `get_unique_patterns_analysis` is cached for 10&nbsp;minutes:

```python
@cache_with_lock(ttl_seconds=600)
def get_unique_patterns_analysis(self, data_source: str | None = None):
    ...
```

Cached results are stored in memory and optionally in Redis if available. Cache
entries expire automatically after the TTL, ensuring that repeated dashboard
requests do not trigger heavy calculations unnecessarily.
