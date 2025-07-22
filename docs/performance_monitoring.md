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

### Circuit Breaker Metrics

Both the Python and Go services expose circuit breaker transitions using the
`circuit_breaker_state_transitions_total` counter. Each transition increments the
counter with labels for the breaker name and new state (`open`, `half_open` or
`closed`). The gateway provides a `/breaker` endpoint that returns the current
counts as JSON and the same metrics are also available via `/metrics` for
Prometheus scraping. Configuration for the breakers lives in
`config/circuit-breakers.yaml` and is loaded by both services.

### Replication Lag Metric

`scripts/replicate_to_timescale.py` exposes a gauge named
`replication_lag_seconds` via Prometheus. The metric records the difference in
seconds between `NOW()` and the timestamp of the most recently replicated access
event. Set the `REPLICATION_METRICS_PORT` environment variable to change the
HTTP port (defaults to `8004`).

### Logstash

`logging/logstash.conf` reads the application, Postgres and Redis logs and can
forward them to Elasticsearch. Start a Logstash container with:

```bash
docker run -p 5044:5044 \
  -v $(pwd)/logging/logstash.conf:/usr/share/logstash/pipeline/logstash.conf \
  docker.elastic.co/logstash/logstash:8
```

Adjust the `elasticsearch` output section if you have a different destination.

### Distributed Tracing

All services export OpenTelemetry traces to Jaeger. Set the `JAEGER_ENDPOINT`
environment variable to the collector URL (`http://localhost:14268/api/traces`
by default). Invoke `init_tracing("analytics-microservice")` during startup of
the analytics microservice so spans are reported correctly.

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

### L1/L2/L3 Cache Levels

The caching subsystem is organised into three tiers managed by
`HierarchicalCacheManager`:

* **L1** – in‑process memory for the fastest access. The maximum number of
  entries is controlled by `CACHE_L1_SIZE`.
* **L2** – a shared Redis cache enabled when `CACHE_TYPE=redis` and configured
  with `CACHE_HOST`, `CACHE_PORT` and `CACHE_DATABASE`.
* **L3** – an optional file‑based cache activated via `CACHE_L3_PATH`. Use
  `CACHE_L3_TTL` to set the expiry for this tier.

`IntelligentCacheWarmer` can prefill these layers on start‑up so the most common
queries are readily available.

## Upcoming Optimization Tools

Several new modules extend the monitoring stack with proactive optimisation
capabilities.

### Optimizer

The upcoming optimizer dynamically tunes analytics batch sizes and caching TTLs.
Enable it with the environment variable `OPTIMIZER_ENABLED=true` and call
`optimizer.start()` during application start-up. The optimizer consults the
`ANALYTICS_CHUNK_SIZE` and `ANALYTICS_MAX_WORKERS` settings to balance CPU and
I/O load.

### Cache Manager

Caching is handled by `MemoryCacheManager` or `RedisCacheManager` from
`config.cache_manager`. Set `CACHE_TYPE=redis` and specify `CACHE_HOST` and
`CACHE_PORT` to store results in Redis.

The `IntelligentMultiLevelCache` combines memory, Redis and disk. Enable it with
`CACHE_TYPE=intelligent` and optionally set `CACHE_DISK_PATH` for the on-disk
layer. The manager promotes entries between levels automatically and exposes a
`report()` method for basic statistics.

```python
from config.cache_manager import get_cache_manager

cache = get_cache_manager()
cache.start()
```

### Memory & CPU Optimizers

Resource optimizers use the environment variables `MAX_MEMORY`,
`MEMORY_WARNING_THRESHOLD`, `MAX_CPU_CORES` and `CPU_WARNING_THRESHOLD` (see
`core/plugins/config/staging.yaml`). When the process exceeds these thresholds,
warnings are logged and background tasks may be throttled.

### Async File Processor

`services.data_processing.async_file_processor.AsyncFileProcessor` loads large
files asynchronously and yields `DataFrame` chunks. Configure chunk size and
memory limits with `ANALYTICS_CHUNK_SIZE` and `ANALYTICS_MAX_MEMORY_MB`.

```python
from services.data_processing.async_file_processor import AsyncFileProcessor

processor = AsyncFileProcessor()
async for chunk in processor.read_csv_chunks("large.csv"):
    handle_chunk(chunk)
```

The processor is registered automatically by `register_upload_services` and used
by the upload workflow.

### Index Optimizer

`database.index_optimizer.IndexOptimizer` inspects how often existing indexes are
used and can generate `CREATE INDEX` statements for missing ones. Run the CLI to
analyze usage or create recommended indexes:

```bash
python -m services.index_optimizer_cli analyze
python -m services.index_optimizer_cli create my_table column_a column_b
```

The CLI relies on `analyze_index_usage()` and `recommend_new_indexes()` to build
SQL statements and execute them against the configured database.

### Load Testing

The repository provides a small Kafka load generator in `tools/load_test.py`.
It publishes synthetic access events at a configurable rate and then queries
Prometheus to determine how many were processed by the gateway event processor.
Run the test locally using the `load-test` target:

```bash
make load-test RATE=100 DURATION=30
```

With the default settings the system should handle more than 2,500 events per
minute while keeping the average processing latency under a second.  Metrics
are scraped from the gateway at `http://localhost:9090` and can be visualised
using the example Grafana dashboard in `dashboards/performance/load_test.json`.
