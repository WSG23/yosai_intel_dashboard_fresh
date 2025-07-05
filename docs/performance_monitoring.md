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

## Plugin Performance Metrics

`EnhancedThreadSafePluginManager` records plugin load times and memory usage.
Metrics are available via `/api/v1/plugins/performance` and the dashboard
components in `components/plugin_performance_dashboard.py`.

