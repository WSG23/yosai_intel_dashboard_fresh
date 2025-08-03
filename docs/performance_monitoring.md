> **Note**: Import paths updated for clean architecture. Legacy imports are deprecated.

# Performance Monitoring

The dashboard collects runtime metrics through the `core.performance` module. A global
`PerformanceMonitor` instance records execution times, memory usage and CPU load.
Use `get_performance_monitor()` to access it and view summaries.

```python
from yosai_intel_dashboard.src.core.performance import get_performance_monitor
summary = get_performance_monitor().get_metrics_summary()
```

 Snapshots are taken automatically in the background and can be visualized or exported
 for further analysis.

## Profiler Setup

Enable the built-in profiler by setting `ENABLE_PROFILING=true`. The flag activates
the request profiling middleware and records CPU and memory usage for each request.
In docker-compose deployments, add the variable under the service environment:

```yaml
services:
  dashboard:
    environment:
      ENABLE_PROFILING: "true"
```

For local development, `deployment/nginx.conf` exposes an optional `/nginx_status`
endpoint to surface basic gateway metrics.

## Query Optimization

PostgreSQL query statistics can be collected with the `pg_stat_statements`
extension. Enable it in the container command and create the extension during
database setup (`deployment/database_setup.sql`):

```yaml
postgres:
  command: ["postgres", "-c", "shared_preload_libraries=pg_stat_statements"]
```

```sql
CREATE EXTENSION IF NOT EXISTS pg_stat_statements;
```

Use `EXPLAIN ANALYZE` with slow queries and add indexes suggested by
`pg_stat_statements` to keep response times low.

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

Additional alert rules can be added under
`monitoring/prometheus/rules/app_alerts.yml`. Typical rules monitor CPU and
memory consumption:

```yaml
- alert: CPUHighUsage
  expr: avg(rate(container_cpu_usage_seconds_total[5m])) by (pod) > 0.8
  for: 5m
  labels:
    severity: warning
  annotations:
    summary: Pod CPU usage above 80% for 5 minutes
- alert: MemoryHighUsage
  expr: container_memory_usage_bytes{image!=""} /
    container_spec_memory_limit_bytes{image!=""} > 0.9
  for: 5m
  labels:
    severity: warning
  annotations:
    summary: Pod memory usage above 90% of limit
```

Grafana can visualise these metrics using the dashboard template in
`monitoring/grafana/dashboards/unified-platform.json`.

## Dashboards

Import the sample Grafana dashboards from `monitoring/grafana/dashboards`
to track request latency, cache hit ratios and load-test throughput. Panels
can be extended with custom PromQL queries to highlight regressions.

## Alerting

Prometheus rule files under `monitoring/prometheus/rules/` provide starter
alert definitions for resource saturation and deprecated function usage.
Route alerts to your paging system or messaging service for timely action.


### Circuit Breaker Metrics

Both the Python and Go services expose circuit breaker transitions using the
`circuit_breaker_state_transitions_total` counter. Each transition increments the
counter with labels for the breaker name and new state (`open`, `half_open` or
`closed`). The gateway provides a `/breaker` endpoint that returns the current
counts as JSON and the same metrics are also available via `/metrics` for
Prometheus scraping. Configuration for the breakers lives in
`config/circuit-breakers.yaml` and is loaded by both services.

### Error Budget Metrics

Each service can expose its remaining error budget via the
`service_error_budget_remaining` gauge and track total errors with
`service_errors_total`. Budgets are configured through the `ERROR_BUDGETS`
environment variable using a comma separated list such as
`api=1000,worker=500`. A default budget of 1000 errors applies when a service
is not explicitly configured.

Applications call `monitoring.error_budget.record_error("service-name")` when
handling exceptions or circuit breaker failures. The helper updates both
metrics and exposes utility functions like `get_remaining_budget` and
`alert_if_exhausted` to integrate with custom alerting systems.

An example Prometheus rule to alert when any service exhausts its error budget
is included in `monitoring/prometheus/rules/app_alerts.yml`:

```yaml
- alert: ErrorBudgetExhausted
  expr: service_error_budget_remaining <= 0
  for: 1m
  labels:
    severity: critical
  annotations:
    summary: Service error budget exhausted
```

### Replication Lag Metric

`scripts/replicate_to_timescale.py` exposes a gauge named
`replication_lag_seconds` via Prometheus. The metric records the difference in
seconds between `NOW()` and the timestamp of the most recently replicated access
event. Set the `REPLICATION_METRICS_PORT` environment variable to change the
HTTP port (defaults to `8004`).

All services expose their runtime metrics at `/metrics` so Prometheus can scrape
them without additional configuration.

### Request Profiling Middleware

Set `ENABLE_PROFILING=true` to enable a middleware that records request latency
and memory usage. The middleware updates the `yosai_request_duration_seconds`
and `yosai_request_memory_mb` Prometheus histograms for every request. Disable
it again with `ENABLE_PROFILING=false`.

### API Request Timing

The API adds a lightweight `TimingMiddleware` that measures how long each
request takes to process. Durations are exported via the
`api_request_duration_seconds` Prometheus histogram and can be scraped from the
`/metrics` endpoint. Values are in seconds and can be aggregated with
`histogram_quantile` to monitor typical latencies (e.g. p95).

Low percentiles close to zero indicate fast responses while higher values or a
steadily increasing trend suggest performance issues with a particular route or
dependency.

### Deprecated Function Usage

Decorate legacy helpers with `@deprecated` from `core` to automatically record
how often they are still invoked.  The decorator emits a Prometheus counter
`deprecated_function_calls_total` with a `function` label and also stores
entries in the global `PerformanceMonitor`.  Example:

```python
from yosai_intel_dashboard.src.core import deprecated

@deprecated("use new_service.process() instead")
def old_process(*args):
    ...
```

Aggregated counts are returned via `get_performance_monitor().get_deprecation_counts()`.
Prioritise migrations by addressing functions with the highest counts first.
Example alerting rules live in `monitoring/prometheus/rules/deprecation_alerts.yml`
and a companion Grafana dashboard in
`dashboards/grafana/deprecation-usage.json`.

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

See [Observability Guide](observability.md) for instructions on viewing logs and traces.

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

### Model Drift Detection

`PerformanceMonitor` includes a helper for simple model drift checks. Pass the
current metrics and the training baseline to `detect_model_drift` to see if any
metric deviates by more than a threshold (default 5%):

```python
from yosai_intel_dashboard.src.core.performance import get_performance_monitor

pm = get_performance_monitor()
baseline = {"accuracy": 0.95, "precision": 0.92, "recall": 0.90}
live = {"accuracy": 0.80, "precision": 0.91, "recall": 0.88}
if pm.detect_model_drift(live, baseline):
    print("Drift detected")

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
requests do not trigger heavy calculations unnecessarily. The TTL values for
analytics results and JWKS lookups are defined in `CacheConfig` (see
`config/base.py`).

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

### Interpreting Cache Metrics

Cache hit and miss counts are exported for Prometheus scraping via the metrics
`dashboard_cache_hits_total` and `dashboard_cache_misses_total`. A healthy
installation should see a hit ratio above **80%** for frequently requested
analytics. A consistently low ratio indicates that the TTL may be too short or
that the workload is too varied for caching to be effective.

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

Upstream services can invalidate stale data by calling `invalidate(key)` to purge
an individual entry from all tiers or `clear(level)` to wipe a specific tier or
the entire cache. These hooks allow microservices to trigger cache purges when
underlying datasets change.

```python
from yosai_intel_dashboard.src.infrastructure.config.cache_manager import get_cache_manager

cache = get_cache_manager()
cache.start()
```

### Memory & CPU Optimizers

Resource optimizers use the environment variables `MAX_MEMORY`,
`MEMORY_WARNING_THRESHOLD`, `MAX_CPU_CORES` and `CPU_WARNING_THRESHOLD` (see
`core/plugins/config/staging.yaml`). When the process exceeds these thresholds,
warnings are logged and background tasks may be throttled.

Garbage collection is tuned globally via `sitecustomize.py`, which sets
`gc.set_threshold(1000, 10, 10)` to reduce the frequency of collections in
long-running services. Short-lived helper scripts can opt out entirely by
setting `SHORT_LIVED_PROCESS=1`; after calling `gc.collect()` the collector is
disabled to avoid unnecessary overhead.

### Async File Processor

`services.data_processing.async_file_processor.AsyncFileProcessor` loads large
files asynchronously and yields `DataFrame` chunks. Configure chunk size and
memory limits with `ANALYTICS_CHUNK_SIZE` and `ANALYTICS_MAX_MEMORY_MB`.

```python
from yosai_intel_dashboard.src.services.data_processing.async_file_processor import AsyncFileProcessor

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

## Load Testing

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

## Psutil and Tracemalloc Profiling

Two helper scripts under `monitoring/` capture runtime resource usage.

* `psutil_profile.py` monitors a running PID or executes a command while recording CPU and memory usage.

  ```bash
  python -m monitoring.psutil_profile 1234 --duration 30 --interval 1 --output profile.json
  ```

  To profile a new command:

  ```bash
  python -m monitoring.psutil_profile python my_script.py --duration 10
  ```

* `tracemalloc_profile.py` runs a Python script with `tracemalloc` enabled and prints the top allocation sites. A snapshot can be saved for later analysis.

  ```bash
  python -m monitoring.tracemalloc_profile scripts/my_job.py --snapshot allocs.snap
  ```

## Troubleshooting and Best Practices

### Interpreting Profiler Output

Spikes in `yosai_request_duration_seconds` often signal slow database calls or
contention on external services. Check the top entries from `psutil_profile.py`
for memory leaks and ensure the process stays below `MAX_MEMORY`.

### Regression Reports

Compare metrics across releases by exporting Prometheus data or running the load
tests on the previous version. Regressions greater than 10% in latency or memory
usage should trigger a review before deployment.

