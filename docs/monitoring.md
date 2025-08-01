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

# Alternatively, compare metrics directly using
# :meth:`PerformanceMonitor.detect_model_drift`:

```python
from yosai_intel_dashboard.src.core.performance import get_performance_monitor

pm = get_performance_monitor()
baseline = {"accuracy": 0.95, "precision": 0.92, "recall": 0.90}
if pm.detect_model_drift(metrics.__dict__, baseline):
    print("Model drift detected")
```
```

To expose the metrics for Prometheus scraping start the server:

```python
from monitoring.prometheus.model_metrics import start_model_metrics_server
start_model_metrics_server(port=9104)
```

`model_accuracy`, `model_precision` and `model_recall` gauges will then be
available on `/metrics`.

## Automated Model Monitoring

`ModelMonitor` evaluates active models at a fixed interval and updates Prometheus metrics.
The interval can be configured in `config/monitoring.yaml` under `model_monitor.evaluation_interval_minutes`.

During each run metrics are checked for drift using `ModelPerformanceMonitor.detect_drift`.
When drift is detected a warning is emitted and the baseline metrics are updated.

```python
from monitoring.model_monitor import ModelMonitor
from models.ml.model_registry import ModelRegistry

registry = ModelRegistry(database_url="sqlite:///models.db", bucket="models")
monitor = ModelMonitor(registry)
monitor.start()
```
