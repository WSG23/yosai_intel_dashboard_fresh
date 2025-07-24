# Model Performance Monitoring

`ModelPerformanceMonitor` tracks accuracy, precision and recall for ML models.
Metrics are forwarded to the global `PerformanceMonitor` and exposed via
Prometheus gauges.

```python
from monitoring.model_performance_monitor import (
    ModelMetrics,
    get_model_performance_monitor,
)

monitor = get_model_performance_monitor()
metrics = ModelMetrics(accuracy=0.95, precision=0.92, recall=0.90)
monitor.log_metrics(metrics)
if monitor.detect_drift(metrics):
    print("Model drift detected")
```

To expose the metrics for Prometheus scraping start the server:

```python
from monitoring.prometheus.model_metrics import start_model_metrics_server
start_model_metrics_server(port=9104)
```

`model_accuracy`, `model_precision` and `model_recall` gauges will then be
available on `/metrics`.
