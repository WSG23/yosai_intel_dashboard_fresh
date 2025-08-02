> **Note**: Import paths updated for clean architecture. Legacy imports are deprecated.

# Model Performance Monitoring

`ModelPerformanceMonitor` tracks accuracy, precision and recall for ML models.
Metrics are forwarded to the global `PerformanceMonitor` and exposed via
Prometheus gauges.

```python
from yosai_intel_dashboard.src.services.monitoring.model_performance_monitor import (
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
from yosai_intel_dashboard.src.services.monitoring.prometheus.model_metrics import start_model_metrics_server
start_model_metrics_server(port=9104)
```

`model_accuracy`, `model_precision`, `model_recall`, `model_f1_score`,
`model_latency_ms`, `model_throughput` and `model_drift_score` gauges will then be
available on `/metrics`.

## Automated Model Monitoring

`ModelMonitor` evaluates active models at a fixed interval and updates Prometheus metrics.
The interval can be configured in `config/monitoring.yaml` under `model_monitor.evaluation_interval_minutes`.

During each run metrics are checked for drift using `ModelPerformanceMonitor.detect_drift`.
When drift is detected a warning is emitted and the baseline metrics are updated.

```python
from yosai_intel_dashboard.src.services.monitoring.model_monitor import ModelMonitor
from yosai_intel_dashboard.src.models.ml.model_registry import ModelRegistry

registry = ModelRegistry(database_url="sqlite:///models.db", bucket="models")
monitor = ModelMonitor(registry)
monitor.start()
```

## Prediction Drift Monitoring

`DriftMonitor` periodically compares live predictions with a baseline
distribution. Each run logs PSI, KS and Wasserstein metrics, stores them via a
user provided callback and triggers alerts when thresholds are exceeded.

```python
from services.monitoring.drift_monitor import DriftMonitor

baseline = get_training_predictions()

monitor = DriftMonitor(
    baseline_supplier=lambda: baseline,
    live_supplier=get_live_predictions,
    thresholds={"psi": 0.2},
    metric_store=save_metrics,
    alert_func=notify_team,
)
monitor.start()
```

Metrics are appended to `monitor.history` and `alert_func` receives the column
name and metric values whenever drift is detected.

## Historical Metrics API

Historic evaluation results can be retrieved via the REST endpoint
`/model-monitoring/{model_name}` which returns metrics stored in TimescaleDB.
