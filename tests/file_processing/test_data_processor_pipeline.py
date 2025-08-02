import importlib.util
import sys
import types
from pathlib import Path

import pandas as pd
import pytest
from tests.import_helpers import safe_import, import_optional

MODULE_PATH = (
    Path(__file__).resolve().parents[2]
    / "yosai_intel_dashboard"
    / "src"
    / "file_processing"
    / "data_processor.py"
)

# Provide minimal stubs for core dependencies before loading the module
truly_stub = types.SimpleNamespace(TrulyUnifiedCallbacks=object)
cb_events_stub = types.SimpleNamespace(
    CallbackEvent=types.SimpleNamespace(SYSTEM_WARNING=1, SYSTEM_ERROR=2)
)
container_stub = types.ModuleType("core.container")
container_stub.get_unicode_processor = lambda: types.SimpleNamespace(
    sanitize_dataframe=lambda df: df
)

sys.modules.setdefault(
    "yosai_intel_dashboard.src.infrastructure.callbacks.unified_callbacks",
    truly_stub,
)
format_stub = types.ModuleType("file_processing.format_detector")


class FormatDetector:
    def __init__(self, *a, **k): ...
    def detect_and_load(self, path, hint=None):
        return pd.read_csv(path), {}


class UnsupportedFormatError(Exception):
    pass


format_stub.FormatDetector = FormatDetector
format_stub.UnsupportedFormatError = UnsupportedFormatError
safe_import('file_processing.format_detector', format_stub)

readers_stub = types.ModuleType("file_processing.readers")
for name in ["CSVReader", "ExcelReader", "JSONReader", "FWFReader", "ArchiveReader"]:
    setattr(readers_stub, name, type(name, (), {}))
safe_import('file_processing.readers', readers_stub)
safe_import('core.callback_events', cb_events_stub)
safe_import('core.container', container_stub)
pkg = types.ModuleType("file_processing")
pkg.__path__ = [str(MODULE_PATH.parent)]
safe_import('file_processing', pkg)
spec = importlib.util.spec_from_file_location(
    "file_processing.data_processor", MODULE_PATH
)
dp_mod = importlib.util.module_from_spec(spec)
safe_import('file_processing.data_processor', dp_mod)
assert spec.loader is not None
spec.loader.exec_module(dp_mod)
DataProcessor = dp_mod.DataProcessor


def test_process_csv_pipeline(tmp_path: Path, monkeypatch):
    df = pd.DataFrame(
        {
            "timestamp": ["2024-01-01 01:02:03"],
            "person_id": ["P1"],
            "badge_id": ["B1"],
            "device_name": ["Entrance"],
            "door_id": ["D1"],
            "access_result": ["granted"],
        }
    )
    csv_path = tmp_path / "d.csv"
    df.to_csv(csv_path, index=False)

    monkeypatch.setattr(DataProcessor, "_enrich_devices", lambda self, d: d)
    monkeypatch.setattr(DataProcessor, "load_file", lambda self, p: pd.read_csv(p))
    monkeypatch.setattr(DataProcessor, "_schema_validate", lambda self, d: d)
    monkeypatch.setattr(
        DataProcessor,
        "_infer_boolean_flags",
        lambda self, d: d.assign(is_entry=False, is_exit=False),
    )

    proc = DataProcessor()
    out = proc.process(str(csv_path))

    required = {
        "timestamp",
        "person_id",
        "badge_id",
        "device_name",
        "door_id",
        "access_result",
        "date",
        "hour_of_day",
        "day_of_week",
        "person_id_valid",
        "badge_id_valid",
        "access_result_code",
        "event_fingerprint",
        "is_entry",
        "is_exit",
        "pipeline_stage",
        "schema_version",
    }
    assert required.issubset(out.columns)
    assert str(out.loc[0, "timestamp"].tzinfo) == "UTC"
    assert out.loc[0, "access_result_code"] == 1
    assert out.loc[0, "pipeline_stage"] == "normalized"
    assert out.loc[0, "schema_version"] == "1.0"


def test_process_excel_pipeline(tmp_path: Path, monkeypatch):
    df = pd.DataFrame(
        {
            "timestamp": ["2024-02-02 10:00:00"],
            "person_id": ["P2"],
            "badge_id": ["B2"],
            "device_name": ["Exit"],
            "door_id": ["D2"],
            "access_result": ["denied"],
        }
    )
    xl_path = tmp_path / "d.xlsx"
    df.to_excel(xl_path, index=False)
    monkeypatch.setattr(DataProcessor, "load_file", lambda self, p: pd.read_excel(p))

    monkeypatch.setattr(DataProcessor, "_enrich_devices", lambda self, d: d)
    monkeypatch.setattr(DataProcessor, "_schema_validate", lambda self, d: d)
    monkeypatch.setattr(
        DataProcessor,
        "_infer_boolean_flags",
        lambda self, d: d.assign(is_entry=False, is_exit=False),
    )

    proc = DataProcessor()
    out = proc.process(str(xl_path))

    assert out.loc[0, "access_result_code"] == 0
    assert out.loc[0, "pipeline_stage"] == "normalized"
    assert out.loc[0, "schema_version"] == "1.0"
