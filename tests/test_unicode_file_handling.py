from datetime import datetime
from pathlib import Path
import importlib.util
import json

import aiofiles
import pandas as pd

helpers_spec = importlib.util.spec_from_file_location(
    "upload_helpers",
    Path(__file__).resolve().parent.parent
    / "yosai_intel_dashboard"
    / "src"
    / "services"
    / "upload"
    / "helpers.py",
)
upload_helpers = importlib.util.module_from_spec(helpers_spec)
helpers_spec.loader.exec_module(upload_helpers)


def test_consolidated_learning_unicode(tmp_path):
    from yosai_intel_dashboard.src.services.learning.src.api.consolidated_service import (
        ConsolidatedLearningService,
    )

    storage = tmp_path / "mäppings.json"
    service = ConsolidatedLearningService(str(storage))

    df = pd.DataFrame(
        {
            "door_id": ["дверь"],
            "timestamp": ["2024-01-01"],
            "user": ["пользователь"],
        }
    )
    mappings = {"дверь": {"floor": 1}}

    service.save_complete_mapping(df, "файл.csv", mappings)

    reloaded = ConsolidatedLearningService(str(storage))
    learned = reloaded.get_learned_mappings(df, "файл.csv")
    assert learned["device_mappings"] == mappings


def test_accessor_load_unicode(tmp_path):
    from yosai_intel_dashboard.src.services.analytics.db_interface import (
        AnalyticsDataAccessor,
    )

    base = tmp_path
    data = {"kéy": "välue"}
    f = base / "learned_mappings.json"
    # write some invalid UTF-8 bytes to ensure errors="replace" works
    with open(f, "wb") as fh:
        fh.write(b'{"k\xe9y": "v\xe4lue"}')

    accessor = AnalyticsDataAccessor(str(base))
    loaded = accessor._load_consolidated_mappings()
    assert loaded
    assert list(loaded.keys())[0].startswith("k")


def test_save_ai_training_data_unicode(tmp_path, monkeypatch):
    from yosai_intel_dashboard.src.components import plugin_adapter

    monkeypatch.setattr(
        plugin_adapter.ComponentPluginAdapter,
        "save_verified_mappings",
        lambda self, *a, **kw: True,
    )

    class DummyDT:
        @classmethod
        def now(cls):
            return datetime(2024, 1, 1, 0, 0, 0)

    monkeypatch.setattr(upload_helpers, "datetime", DummyDT)

    upload_helpers.save_ai_training_data(
        "файл.csv",
        {"дверь": "timestamp"},
        {"columns": ["a"], "ai_suggestions": {}},
    )

    target = Path("data/training/mappings_20240101.jsonl")
    content = target.read_text(encoding="utf-8")
    data = json.loads(content)
    assert data["filename"] == "файл.csv"
    assert "дверь" in data["mappings"]
    target.unlink()
    target.parent.rmdir()
