"""
Test suite for consolidated learning service.
"""

import tempfile
from pathlib import Path

import pandas as pd

from yosai_intel_dashboard.src.services.learning.src.api.consolidated_service import ConsolidatedLearningService


class TestConsolidatedLearningService:

    def setup_method(self):
        self.temp_dir = tempfile.mkdtemp()
        self.storage_path = Path(self.temp_dir) / "test_mappings.json"
        self.service = ConsolidatedLearningService(str(self.storage_path))

    def test_save_and_retrieve_exact_match(self):
        df = pd.DataFrame(
            {
                "door_id": ["door_1", "door_2"],
                "timestamp": ["2024-01-01", "2024-01-02"],
                "user": ["user_a", "user_b"],
            }
        )
        device_mappings = {
            "door_1": {"floor": 1, "security": 5},
            "door_2": {"floor": 2, "security": 7},
        }
        fingerprint = self.service.save_complete_mapping(
            df, "test_file.csv", device_mappings
        )
        assert len(fingerprint) == 32
        learned = self.service.get_learned_mappings(df, "test_file.csv")
        assert learned["match_type"] == "exact"
        assert learned["device_mappings"] == device_mappings
        assert learned["confidence"] == 1.0

    def test_similarity_matching(self):
        df1 = pd.DataFrame(
            {"door_id": ["door_1"], "timestamp": ["2024-01-01"], "user": ["user_a"]}
        )
        device_mappings = {"door_1": {"floor": 1, "security": 5}}
        self.service.save_complete_mapping(df1, "file1.csv", device_mappings)

        df2 = pd.DataFrame(
            {"door_id": ["door_2"], "timestamp": ["2024-01-02"], "user": ["user_b"]}
        )
        learned = self.service.get_learned_mappings(df2, "file2.csv")
        assert learned["match_type"] == "similar"
        assert learned["device_mappings"] == device_mappings
        assert 0.7 <= learned["confidence"] <= 1.0

    def test_no_match_found(self):
        df = pd.DataFrame({"completely_different": ["data"], "columns": ["here"]})
        learned = self.service.get_learned_mappings(df, "new_file.csv")
        assert learned["match_type"] == "none"
        assert learned["device_mappings"] == {}
        assert learned["confidence"] == 0.0

    def test_learning_statistics(self):
        stats = self.service.get_learning_statistics()
        assert stats["total_mappings"] == 0
        df = pd.DataFrame({"door_id": ["door_1", "door_2"]})
        self.service.save_complete_mapping(df, "test.csv", {})
        stats = self.service.get_learning_statistics()
        assert stats["total_mappings"] == 1
        assert len(stats["files"]) == 1
        assert stats["files"][0]["filename"] == "test.csv"

    def test_persist_and_load_mappings(self):
        """Mappings should persist to disk and load in new instance."""
        df = pd.DataFrame({"door_id": ["door_1"]})
        mappings = {"door_1": {"floor": 1}}
        self.service.save_complete_mapping(df, "persist.csv", mappings)

        assert self.storage_path.exists()

        reloaded = ConsolidatedLearningService(str(self.storage_path))
        learned = reloaded.get_learned_mappings(df, "persist.csv")
        assert learned["match_type"] == "exact"
        assert learned["device_mappings"] == mappings

    def test_apply_to_global_store(self):
        """Applying learned mappings should update the global store."""
        from yosai_intel_dashboard.src.services.ai_mapping_store import ai_mapping_store

        df = pd.DataFrame({"door_id": ["door_1"]})
        mappings = {"door_1": {"floor": 2}}
        ai_mapping_store.clear()
        self.service.save_complete_mapping(df, "apply.csv", mappings)

        applied = self.service.apply_to_global_store(df, "apply.csv")
        assert applied is True
        assert ai_mapping_store.all() == mappings

    def teardown_method(self):
        if self.storage_path.exists():
            self.storage_path.unlink()

    def test_ignore_legacy_pickle(self):
        """Service should not migrate or delete legacy pickle files."""
        import pickle

        pkl_path = self.storage_path.with_suffix(".pkl")
        with open(pkl_path, "wb") as fh:
            pickle.dump({"old": "data"}, fh)

        service = ConsolidatedLearningService(str(self.storage_path))
        assert service.learned_data == {}
        assert pkl_path.exists()

    def test_json_precedence_over_pickle(self):
        import json
        import pickle

        json_content = {"foo": "bar"}
        with open(self.storage_path, "w", encoding="utf-8") as fh:
            json.dump(json_content, fh)

        pkl_path = self.storage_path.with_suffix(".pkl")
        with open(pkl_path, "wb") as fh:
            pickle.dump({"legacy": True}, fh)

        service = ConsolidatedLearningService(str(self.storage_path))
        assert service.learned_data == json_content
        assert pkl_path.exists()

    def test_save_column_mappings(self):
        df = pd.DataFrame({"a": [1], "b": [2]})
        cols = {"a": "door_id", "b": "timestamp"}
        fingerprint = self.service.save_complete_mapping(df, "cols.csv", {}, cols)
        reloaded = ConsolidatedLearningService(str(self.storage_path))
        assert fingerprint in reloaded.learned_data
        assert reloaded.learned_data[fingerprint]["column_mappings"] == cols
