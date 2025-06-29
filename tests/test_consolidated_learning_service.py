"""
Test suite for consolidated learning service.
"""
import pandas as pd
import tempfile
from pathlib import Path
from services.consolidated_learning_service import ConsolidatedLearningService

class TestConsolidatedLearningService:

    def setup_method(self):
        self.temp_dir = tempfile.mkdtemp()
        self.storage_path = Path(self.temp_dir) / "test_mappings.json"
        self.service = ConsolidatedLearningService(str(self.storage_path))

    def test_save_and_retrieve_exact_match(self):
        df = pd.DataFrame({
            'door_id': ['door_1', 'door_2'],
            'timestamp': ['2024-01-01', '2024-01-02'],
            'user': ['user_a', 'user_b']
        })
        device_mappings = {
            'door_1': {'floor': 1, 'security': 5},
            'door_2': {'floor': 2, 'security': 7}
        }
        fingerprint = self.service.save_complete_mapping(df, "test_file.csv", device_mappings)
        assert len(fingerprint) == 32
        learned = self.service.get_learned_mappings(df, "test_file.csv")
        assert learned['match_type'] == 'exact'
        assert learned['device_mappings'] == device_mappings
        assert learned['confidence'] == 1.0

    def test_similarity_matching(self):
        df1 = pd.DataFrame({
            'door_id': ['door_1'],
            'timestamp': ['2024-01-01'],
            'user': ['user_a']
        })
        device_mappings = {'door_1': {'floor': 1, 'security': 5}}
        self.service.save_complete_mapping(df1, "file1.csv", device_mappings)

        df2 = pd.DataFrame({
            'door_id': ['door_2'],
            'timestamp': ['2024-01-02'],
            'user': ['user_b']
        })
        learned = self.service.get_learned_mappings(df2, "file2.csv")
        assert learned['match_type'] == 'similar'
        assert learned['device_mappings'] == device_mappings
        assert 0.7 <= learned['confidence'] <= 1.0

    def test_no_match_found(self):
        df = pd.DataFrame({
            'completely_different': ['data'],
            'columns': ['here']
        })
        learned = self.service.get_learned_mappings(df, "new_file.csv")
        assert learned['match_type'] == 'none'
        assert learned['device_mappings'] == {}
        assert learned['confidence'] == 0.0

    def test_learning_statistics(self):
        stats = self.service.get_learning_statistics()
        assert stats['total_mappings'] == 0
        df = pd.DataFrame({'door_id': ['door_1', 'door_2']})
        self.service.save_complete_mapping(df, "test.csv", {})
        stats = self.service.get_learning_statistics()
        assert stats['total_mappings'] == 1
        assert len(stats['files']) == 1
        assert stats['files'][0]['filename'] == "test.csv"

    def test_persist_and_load_mappings(self):
        """Mappings should persist to disk and load in new instance."""
        df = pd.DataFrame({'door_id': ['door_1']})
        mappings = {'door_1': {'floor': 1}}
        self.service.save_complete_mapping(df, 'persist.csv', mappings)

        assert self.storage_path.exists()

        reloaded = ConsolidatedLearningService(str(self.storage_path))
        learned = reloaded.get_learned_mappings(df, 'persist.csv')
        assert learned['match_type'] == 'exact'
        assert learned['device_mappings'] == mappings

    def test_apply_to_global_store(self):
        """Applying learned mappings should update the global store."""
        from services.ai_mapping_store import ai_mapping_store

        df = pd.DataFrame({'door_id': ['door_1']})
        mappings = {'door_1': {'floor': 2}}
        ai_mapping_store.clear()
        self.service.save_complete_mapping(df, 'apply.csv', mappings)

        applied = self.service.apply_to_global_store(df, 'apply.csv')
        assert applied is True
        assert ai_mapping_store.all() == mappings

    def teardown_method(self):
        if self.storage_path.exists():
            self.storage_path.unlink()
