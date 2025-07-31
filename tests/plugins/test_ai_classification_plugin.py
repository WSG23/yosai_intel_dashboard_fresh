import importlib.util
import sys
import types
from pathlib import Path
from unittest.mock import MagicMock


def _install_core_stub(monkeypatch):
    core_pkg = types.ModuleType("core")
    core_pkg.__path__ = []
    protocols_pkg = types.ModuleType("core.protocols")
    plugin_pkg = types.ModuleType("core.protocols.plugin")

    class PluginMetadata:
        def __init__(self, name, version, description, author):
            self.name = name
            self.version = version
            self.description = description
            self.author = author

    plugin_pkg.PluginMetadata = PluginMetadata
    protocols_pkg.plugin = plugin_pkg
    core_pkg.protocols = protocols_pkg
    monkeypatch.setitem(sys.modules, "core", core_pkg)
    monkeypatch.setitem(sys.modules, "core.protocols", protocols_pkg)
    monkeypatch.setitem(sys.modules, "core.protocols.plugin", plugin_pkg)


def _load_ai_plugin(monkeypatch, repo_success=True):
    _install_core_stub(monkeypatch)
    path = Path("plugins/ai_classification/plugin.py")
    import importlib

    pkg = importlib.import_module("plugins.ai_classification")
    spec = importlib.util.spec_from_file_location(
        "plugins.ai_classification.plugin", path
    )
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    pkg.plugin = module

    repo = MagicMock()
    repo.initialize.return_value = repo_success
    repo_mod = types.ModuleType("plugins.ai_classification.database.csv_storage")
    repo_mod.CSVStorageRepository = lambda p: repo
    sys.modules["plugins.ai_classification.database.csv_storage"] = repo_mod

    service_names = {
        "column_mapper": "ColumnMappingService",
        "csv_processor": "CSVProcessorService",
        "entry_classifier": "EntryClassificationService",
        "floor_estimator": "FloorEstimationService",
        "japanese_handler": "JapaneseTextHandler",
    }
    for mod_name, cls in service_names.items():
        m = types.ModuleType(f"plugins.ai_classification.services.{mod_name}")
        setattr(m, cls, object)
        sys.modules[f"plugins.ai_classification.services.{mod_name}"] = m

    spec.loader.exec_module(module)
    return module.AIClassificationPlugin, repo


def test_start_initializes_services(monkeypatch, mock_auth_env):
    stub_preview = types.ModuleType("utils.preview_utils")
    stub_preview.serialize_dataframe_preview = lambda df: []
    monkeypatch.setitem(sys.modules, "utils.preview_utils", stub_preview)
    AIClassificationPlugin, repo = _load_ai_plugin(monkeypatch, repo_success=True)
    monkeypatch.setattr(
        "plugins.ai_classification.plugin.JapaneseTextHandler", lambda cfg: "japan"
    )
    monkeypatch.setattr(
        "plugins.ai_classification.plugin.CSVProcessorService",
        lambda r, j, c: "processor",
    )
    monkeypatch.setattr(
        "plugins.ai_classification.plugin.ColumnMappingService", lambda r, c: "mapper"
    )
    monkeypatch.setattr(
        "plugins.ai_classification.plugin.FloorEstimationService", lambda r, c: "floor"
    )
    monkeypatch.setattr(
        "plugins.ai_classification.plugin.EntryClassificationService",
        lambda r, c: "entry",
    )

    plugin = AIClassificationPlugin()
    assert plugin.start() is True
    assert plugin.is_started
    assert plugin.csv_repository is repo
    assert plugin.csv_processor == "processor"
    assert plugin.column_mapper == "mapper"
    assert plugin.floor_estimator == "floor"
    assert plugin.entry_classifier == "entry"
    expected_services = {
        "process_csv",
        "map_columns",
        "confirm_mapping",
        "estimate_floors",
        "classify_entries",
        "confirm_device_mapping",
        "get_session_data",
        "save_permanent_data",
    }
    assert set(plugin.services.keys()) == expected_services
    repo.initialize.assert_called_once()


def test_start_failure_logs_error(monkeypatch, caplog, mock_auth_env):
    stub_preview = types.ModuleType("utils.preview_utils")
    stub_preview.serialize_dataframe_preview = lambda df: []
    monkeypatch.setitem(sys.modules, "utils.preview_utils", stub_preview)
    AIClassificationPlugin, repo = _load_ai_plugin(monkeypatch, repo_success=False)

    plugin = AIClassificationPlugin()
    with caplog.at_level("ERROR"):
        result = plugin.start()

    assert result is False
    assert not plugin.is_started
    assert any(
        "failed to start plugin" in record.getMessage() for record in caplog.records
    )
