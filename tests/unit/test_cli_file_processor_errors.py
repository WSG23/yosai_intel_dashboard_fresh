import sys
import types

import pytest

from src.exceptions import FileProcessingError


def test_process_file_missing(monkeypatch, tmp_path):
    # stub minimal dependencies to import cli_file_processor
    safe_module = types.ModuleType("yosai_intel_dashboard.src.utils.text_utils")
    safe_module.safe_text = lambda x: str(x)
    monkeypatch.setitem(sys.modules, "yosai_intel_dashboard", types.ModuleType("yosai_intel_dashboard"))
    monkeypatch.setitem(sys.modules, "yosai_intel_dashboard.src", types.ModuleType("yosai_intel_dashboard.src"))
    monkeypatch.setitem(sys.modules, "yosai_intel_dashboard.src.utils", types.ModuleType("yosai_intel_dashboard.src.utils"))
    monkeypatch.setitem(
        sys.modules, "yosai_intel_dashboard.src.utils.text_utils", safe_module
    )
    monkeypatch.setitem(sys.modules, "sklearn", types.ModuleType("sklearn"))
    ensemble = types.ModuleType("sklearn.ensemble")
    ensemble.IsolationForest = object
    monkeypatch.setitem(sys.modules, "sklearn.ensemble", ensemble)

    from tools.cli_file_processor import process_file_simple

    missing = tmp_path / "missing.csv"
    with pytest.raises(FileProcessingError):
        process_file_simple(str(missing))
