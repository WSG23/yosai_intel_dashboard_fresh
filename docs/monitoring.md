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

## ModelPerformanceTracker Usage

`ModelPerformanceTracker` keeps a running log of per-inference metrics and pushes updates to the global monitor.

```python
from yosai_intel_dashboard.src.services.monitoring.model_performance_tracker import (
    ModelPerformanceTracker,
)

tracker = ModelPerformanceTracker(baseline={"accuracy": 0.94})
tracker.record(y_true, y_pred)
tracker.export(port=9104)
```

The tracker aggregates metrics and updates the Prometheus gauges in real time.

## Alert Configuration

Alerts are configured via the `AlertConfig` dataclass and dispatched by `AlertDispatcher`.

```python
from yosai_intel_dashboard.src.core.monitoring.user_experience_metrics import (
    AlertConfig,
    AlertDispatcher,
)

config = AlertConfig(
    slack_webhook="https://hooks.slack.com/services/T000/B000/XXX",
    email="ml-alerts@example.com",
    webhook_url="https://hooks.example.com/monitor",
)
dispatcher = AlertDispatcher(config)
dispatcher.send_alert("Model accuracy dropped below threshold")
```

Prometheus alerting rules can be customized in `monitoring/prometheus/rules/app_alerts.yml` to fire when metrics exceed the defined thresholds.

## Visualization Examples

Metrics scraped by Prometheus can be visualized using common Python tools.

```python
from datetime import datetime, timedelta

import matplotlib.pyplot as plt
from prometheus_api_client import PrometheusConnect

pc = PrometheusConnect(url="http://localhost:9090", disable_ssl=True)
end = datetime.utcnow()
start = end - timedelta(hours=1)
series = pc.get_metric_range_data("model_accuracy", start, end)
times = [point[0] for point in series[0]["values"]]
values = [float(point[1]) for point in series[0]["values"]]
plt.plot(times, values)
plt.title("Model Accuracy (last hour)")
plt.show()
```

## A/B Testing and Model Versioning Workflows

Run experiments across model versions and manage deployments.

```python
from yosai_intel_dashboard.src.models.ml import ModelRegistry
from yosai_intel_dashboard.src.services.ab_testing import ModelABTester

registry = ModelRegistry("sqlite:///registry.db", "ml-bucket")
tester = ModelABTester("fraud-model", registry, weights={"1.0.0": 50, "1.1.0": 50})
prediction = tester.predict(data)
```

```python
from yosai_intel_dashboard.src.models.ml.model_registry import ModelRegistry

registry = ModelRegistry("sqlite:///models.db", bucket="models")
registry.register("fraud-model", "1.2.0", artifact_path="model.joblib")
registry.activate("fraud-model", "1.2.0")
```

## Integration Endpoints

- [Prometheus metrics](http://localhost:9104/metrics)
- [WebSocket stream](ws://localhost:6789)
- [REST metrics](http://localhost:8000/api/metrics)

