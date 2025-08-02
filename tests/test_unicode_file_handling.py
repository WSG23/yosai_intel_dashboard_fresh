import builtins
from datetime import datetime

import pandas as pd

import yosai_intel_dashboard.src.services as services.upload.helpers as upload_helpers
from yosai_intel_dashboard.src.services.analytics.db_interface import AnalyticsDataAccessor
from yosai_intel_dashboard.src.services.learning.src.api.consolidated_service import ConsolidatedLearningService
from yosai_intel_dashboard.src.services.upload import save_ai_training_data


def test_consolidated_learning_unicode(tmp_path):
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
    training_dir = tmp_path / "training"
    training_dir.mkdir()

    target = training_dir / "out.jsonl"

    def fake_makedirs(path, exist_ok=False):
        training_dir.mkdir(exist_ok=True)

    monkeypatch.setattr(upload_helpers.os, "makedirs", fake_makedirs)

    open_orig = builtins.open

    def fake_open(path, mode="r", encoding=None, errors=None):
        if path.startswith("data/training"):
            return open_orig(target, mode, encoding=encoding, errors=errors)
        return open_orig(path, mode, encoding=encoding, errors=errors)

    monkeypatch.setattr(upload_helpers, "open", fake_open)

    class DummyDT:
        @classmethod
        def now(cls):
            return datetime(2024, 1, 1, 0, 0, 0)

    monkeypatch.setattr(upload_helpers, "datetime", DummyDT)

    save_ai_training_data(
        "файл.csv",
        {"дверь": "timestamp"},
        {"columns": ["a"], "ai_suggestions": {}},
    )

    content = target.read_text(encoding="utf-8")
    assert "файл.csv" in content
    assert "дверь" in content
