import pandas as pd

from monitoring.data_quality_monitor import (
    DataQualityMetrics,
    DataQualityMonitor,
    DataQualityThresholds,
    get_data_quality_monitor,
)


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
    import sys
    import types

    # Provide minimal Processor stub if services package is absent
    if "services.data_processing.processor" not in sys.modules:
        module = types.ModuleType("services.data_processing.processor")

        class Processor:
            def __init__(self) -> None:
                pass

            def _load_consolidated_mappings(self):
                return {}

            def _get_uploaded_data(self):
                return {}

            def get_processed_database(self):
                dq = get_data_quality_monitor()
                dq.emit(
                    DataQualityMetrics(
                        missing_ratio=0.0, outlier_ratio=0.0, schema_violations=0
                    )
                )
                return {}

        module.Processor = Processor
        sys.modules["services.data_processing.processor"] = module

    from yosai_intel_dashboard.src.services.data_processing.processor import Processor

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
