import types
import pytest

# Robust import path handling
try:
    from yosai_intel_dashboard.src.models.ml import training as training_pkg
except Exception:
    try:
        from src.models.ml import training as training_pkg
    except Exception:
        import sys
        import pathlib

        repo_root = pathlib.Path(__file__).resolve().parents[1]
        sys.path.append(str(repo_root))
        from src.models.ml import training as training_pkg  # type: ignore


def test_pipeline_dask_cluster_fail(monkeypatch):
    """
    Simulates Dask cluster creation failure and verifies the error propagates
    (so callers can react) while our code still executes the 'finally' path.
    """
    pipeline_mod = training_pkg.pipeline

    # Force the distributed branch to be taken and cluster creation attempted
    class FakeClient:
        def __init__(self, *a, **k):
            pass

        def close(self):
            pass

    class FakeBackend:
        def __init__(self, *a, **k):
            pass

        def __enter__(self):
            return self

        def __exit__(self, exc_type, exc, tb):
            return False

    calls = {"cluster_attempted": False}

    def fake_cluster(*args, **kwargs):
        calls["cluster_attempted"] = True
        raise RuntimeError("Cluster init failed")

    # Monkeypatch Dask symbols to ensure the guarded path is entered
    monkeypatch.setattr(pipeline_mod, "DaskClient", FakeClient, raising=True)
    monkeypatch.setattr(
        pipeline_mod, "JoblibParallelBackend", FakeBackend, raising=True
    )
    monkeypatch.setattr(pipeline_mod, "DaskLocalCluster", fake_cluster, raising=True)

    # Minimal registry stub if the pipeline expects it
    DummyReg = types.SimpleNamespace(
        get_model=lambda *a, **k: None,
        _metrics_improved=lambda *a, **k: True,
        register_model=lambda name, path, metrics, dataset_hash: types.SimpleNamespace(
            version=1
        ),
        set_active_version=lambda name, version: None,
    )

    # Build pipeline instance; distributed=True to trigger dask branch
    TP = pipeline_mod.TrainingPipeline
    pipeline = TP(registry=DummyReg, distributed=True)

    # Use a dummy estimator and minimal data; the exception occurs before training
    with pytest.raises(RuntimeError, match="Cluster init failed"):
        pipeline._train_single(
            "modelX",
            estimator=object(),
            param_space={},
            X=[[0]],
            y=[0],
            dataset_hash="hash",
        )

    assert calls["cluster_attempted"] is True


# Optional: ensure code does not attempt Dask when components are missing


def test_pipeline_runs_without_dask_when_unavailable(monkeypatch):
    pipeline_mod = training_pkg.pipeline

    # Ensure Dask symbols are None/unavailable
    monkeypatch.setattr(pipeline_mod, "DaskClient", None, raising=True)
    monkeypatch.setattr(pipeline_mod, "DaskLocalCluster", None, raising=True)
    monkeypatch.setattr(pipeline_mod, "JoblibParallelBackend", None, raising=True)

    TP = pipeline_mod.TrainingPipeline

    # Stub out expensive training step
    def fake_tune(self, estimator, param_space, X, y):
        return "OK"

    monkeypatch.setattr(TP, "_tune_hyperparams", fake_tune, raising=True)

    pipeline = TP(registry=None, distributed=True)
    # Should not raise; falls back to local path
    pipeline._train_single(
        "modelY",
        estimator=object(),
        param_space={},
        X=[[1]],
        y=[1],
        dataset_hash="hash2",
    )
