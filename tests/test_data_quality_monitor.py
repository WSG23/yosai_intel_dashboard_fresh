import pandas as pd
from monitoring.data_quality_monitor import (
    DataQualityMonitor,
    DataQualityMetrics,
    DataQualityThresholds,
)
from monitoring.data_quality_monitor import get_data_quality_monitor


def test_data_quality_monitor_alert(monkeypatch):
    dispatcher_calls = []
    monitor = DataQualityMonitor(
        thresholds=DataQualityThresholds(
            max_missing_ratio=0.0, max_outlier_ratio=0.0, max_schema_violations=0
        )
    )
    monkeypatch.setattr(
        monitor.dispatcher, "send_alert", lambda msg: dispatcher_calls.append(msg)
    )
    metrics = DataQualityMetrics(
        missing_ratio=0.5, outlier_ratio=0.1, schema_violations=1
    )
    monitor.emit(metrics)
    assert dispatcher_calls


def test_processor_evaluates_quality(monkeypatch):
    from services.data_processing.processor import Processor

    proc = Processor()
    df = pd.DataFrame(
        {
            "timestamp": [1, 2, None],
            "person_id": ["a", "b", "c"],
            "door_id": ["d1", "d2", "d3"],
            "access_result": [1, 1, 1],
            "value": [0, 1000, 0],
        }
    )
    metrics_list = []
    monkeypatch.setattr(
        "monitoring.data_quality_monitor.get_data_quality_monitor",
        lambda: DataQualityMonitor(thresholds=DataQualityThresholds()),
    )
    dq = get_data_quality_monitor()
    monkeypatch.setattr(dq, "emit", lambda m: metrics_list.append(m))
    monkeypatch.setattr(proc, "_load_consolidated_mappings", lambda: {})
    monkeypatch.setattr(proc, "_get_uploaded_data", lambda: {"f.csv": df})
    proc.get_processed_database()
    assert metrics_list
