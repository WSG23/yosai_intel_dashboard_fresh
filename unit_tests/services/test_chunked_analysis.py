import logging
import types
import importlib
import sys
import builtins

import pandas as pd

# Stub heavy dependencies before importing the module under test
sys.modules.setdefault(
    "validation.data_validator", types.SimpleNamespace(DataValidator=object)
)
sys.modules.setdefault(
    "validation.security_validator", types.SimpleNamespace(SecurityValidator=object)
)
sys.modules.setdefault(
    "yosai_intel_dashboard.src.infrastructure.config.config",
    types.SimpleNamespace(get_analytics_config=lambda: None),
)
sys.modules.setdefault(
    "yosai_intel_dashboard.src.services.result_formatting",
    types.SimpleNamespace(regular_analysis=lambda df, types: {}),
)


class ChunkedAnalyticsController:  # minimal stub for type hints
    pass

builtins.ChunkedAnalyticsController = ChunkedAnalyticsController
sys.modules.setdefault(
    "yosai_intel_dashboard.src.services.analytics.chunked_analytics_controller",
    types.SimpleNamespace(ChunkedAnalyticsController=ChunkedAnalyticsController),
)

ca = importlib.import_module("yosai_intel_dashboard.src.services.chunked_analysis")


class DummyController:
    """Minimal controller to exercise ``_process_chunks``."""

    def _chunk_dataframe(self, df: pd.DataFrame):
        mid = len(df) // 2
        yield df.iloc[:mid]
        yield df.iloc[mid:]

    def _process_chunk(self, chunk_df: pd.DataFrame, analysis_types):
        return {"total": int(chunk_df["val"].sum())}

    def _create_empty_results(self):
        return {"total": 0}

    def _aggregate_results(self, agg, res):
        agg["total"] += res["total"]

    def _finalize_results(self, agg):
        return agg


def _expected(df: pd.DataFrame, controller: DummyController):
    """Compute expected aggregation sequentially."""

    chunks = list(controller._chunk_dataframe(df))
    aggregated = controller._create_empty_results()
    aggregated.update({"date_range": {"start": None, "end": None}, "rows_processed": 0})
    for chunk in chunks:
        res = controller._process_chunk(chunk, [])
        controller._aggregate_results(aggregated, res)
        aggregated["rows_processed"] += len(chunk)
    return controller._finalize_results(aggregated)


def _make_df():
    return pd.DataFrame({"val": [1, 2, 3, 4]})


def test_process_chunks_with_dask(monkeypatch, tmp_path):
    df = _make_df()
    controller = DummyController()

    def delayed(fn):
        def wrapper(*a, **k):
            return lambda: fn(*a, **k)

        return wrapper

    def compute(*tasks):
        return [t() for t in tasks]

    dummy_dask = types.SimpleNamespace(delayed=delayed, compute=compute)

    class DummyCluster:
        called = False

        def __init__(self, *a, **k):
            DummyCluster.called = True

        def close(self):  # pragma: no cover - simple stub
            pass

    class DummyClient:
        called = False

        def __init__(self, *a, **k):
            DummyClient.called = True

        def close(self):  # pragma: no cover - simple stub
            pass

    monkeypatch.setattr(ca, "dask", dummy_dask)
    monkeypatch.setattr(ca, "LocalCluster", DummyCluster)
    monkeypatch.setattr(ca, "Client", DummyClient)

    result = ca._process_chunks(df, controller, [], tmp_path, max_workers=2)

    assert DummyCluster.called and DummyClient.called
    assert result == _expected(df, controller)


def test_process_chunks_without_dask(monkeypatch, tmp_path, caplog):
    df = _make_df()
    controller = DummyController()

    monkeypatch.setattr(ca, "dask", None)
    monkeypatch.setattr(ca, "LocalCluster", None)
    monkeypatch.setattr(ca, "Client", None)

    caplog.set_level(logging.INFO)
    result = ca._process_chunks(df, controller, [], tmp_path, max_workers=2)

    assert result == _expected(df, controller)
    assert "distributed path" in caplog.text.lower()
