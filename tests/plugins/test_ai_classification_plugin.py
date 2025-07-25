import types
from unittest.mock import MagicMock

import pytest

from yosai_intel_dashboard.src.plugins.ai_classification.plugin import AIClassificationPlugin


def test_start_initializes_services(monkeypatch):
    repo = MagicMock()
    repo.initialize.return_value = True

    monkeypatch.setattr(
        "plugins.ai_classification.plugin.CSVStorageRepository", lambda path: repo
    )
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
