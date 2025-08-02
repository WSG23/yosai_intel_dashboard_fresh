import hashlib
import json
import os
import pickle
import sys
import types

import pandas as pd
import pytest
from tests.import_helpers import safe_import, import_optional

# Stub heavy optional dependencies before importing the services package
safe_import('scipy', types.ModuleType("scipy"))
sys.modules["scipy"].stats = types.SimpleNamespace()

import importlib.util
from pathlib import Path

# Load chunked_analysis without importing the entire services package
module_path = Path(__file__).resolve().parents[2] / "services" / "chunked_analysis.py"
spec = importlib.util.spec_from_file_location("services.chunked_analysis", module_path)
services_pkg = types.ModuleType("services")
services_pkg.__path__ = [str(module_path.parent)]
safe_import('services', services_pkg)
chunk_mod = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = chunk_mod
spec.loader.exec_module(chunk_mod)

analyze_with_chunking = chunk_mod.analyze_with_chunking
from yosai_intel_dashboard.src.services.analytics.chunked_analytics_controller import ChunkedAnalyticsController
from validation.security_validator import SecurityValidator


class DummyCluster:
    def __init__(self, *a, **k):
        pass

    def close(self):
        pass


class DummyClient:
    def __init__(self, *a, **k):
        pass

    def close(self):
        pass


def _chunk_key(df: pd.DataFrame) -> str:
    digest = hashlib.sha256(
        pd.util.hash_pandas_object(df, index=True).values.tobytes()
    ).hexdigest()
    return digest


def _simple_df():
    return pd.DataFrame(
        {
            "Person ID": ["u1", "u2"],
            "Device name": ["d1", "d2"],
            "Access result": ["Granted", "Denied"],
        }
    )


def test_json_cache_roundtrip(tmp_path, monkeypatch):
    df = _simple_df()
    monkeypatch.setenv("CHUNK_CACHE_DIR", str(tmp_path))
    validator = SecurityValidator()

    class Cfg:
        chunk_size = len(df)
        max_workers = 1

    monkeypatch.setattr(chunk_mod, "get_analytics_config", lambda: Cfg())
    monkeypatch.setattr(chunk_mod, "LocalCluster", DummyCluster)
    monkeypatch.setattr(chunk_mod, "Client", DummyClient)
    monkeypatch.setattr(
        chunk_mod.dask, "compute", lambda *ts: [t.compute(scheduler="sync") for t in ts]
    )
    first = analyze_with_chunking(df, validator, [])
    files = list(tmp_path.glob("*.json"))
    assert len(files) == 1

    def boom(*args, **kwargs):
        raise AssertionError("processing should not occur")

    monkeypatch.setattr(ChunkedAnalyticsController, "_process_chunk", boom)
    second = analyze_with_chunking(df, validator, [])
    assert first == second


def test_cache_rejects_pickle(tmp_path, monkeypatch):
    df = _simple_df()
    monkeypatch.setenv("CHUNK_CACHE_DIR", str(tmp_path))
    key = _chunk_key(df)
    cache_file = tmp_path / f"{key}.json"

    evil_file = tmp_path / "evil_triggered"

    class Exploit:
        def __reduce__(self):
            import builtins

            return (builtins.exec, (f"open('{evil_file}', 'w').close()",))

    cache_file.write_bytes(pickle.dumps(Exploit()))

    validator = SecurityValidator()

    class Cfg:
        chunk_size = len(df)
        max_workers = 1

    monkeypatch.setattr(chunk_mod, "get_analytics_config", lambda: Cfg())
    monkeypatch.setattr(chunk_mod, "LocalCluster", DummyCluster)
    monkeypatch.setattr(chunk_mod, "Client", DummyClient)
    monkeypatch.setattr(
        chunk_mod.dask, "compute", lambda *ts: [t.compute(scheduler="sync") for t in ts]
    )
    with pytest.raises((json.JSONDecodeError, UnicodeDecodeError)):
        analyze_with_chunking(df, validator, [])
    assert not evil_file.exists()
