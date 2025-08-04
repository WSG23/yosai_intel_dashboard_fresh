from examples.debug_deep_analytics import (
from yosai_intel_dashboard.src.core.imports.resolver import safe_import
    check_upload_store,
    create_test_dataset,
    find_hardcoded_values,
)


def test_create_test_dataset():
    df = create_test_dataset(10)
    assert len(df) == 10
    assert list(df.columns) == ["person_id", "door_id", "access_result", "timestamp"]


def test_check_upload_store(tmp_path, monkeypatch):
    import sys
    import types

    class DummyStore:
        def __init__(self):
            self.data = {}

        def add_file(self, filename, df):
            self.data[filename] = df

        def get_all_data(self):
            return self.data

        def clear_all(self):
            self.data = {}

    dummy_module = types.ModuleType("utils.upload_store")
    dummy_store = DummyStore()
    dummy_module.UploadedDataStore = DummyStore
    dummy_module.uploaded_data_store = dummy_store
    safe_import('utils.upload_store', dummy_module)

    df = create_test_dataset(5)
    stored = check_upload_store(df)
    assert stored is not None
    assert len(stored) == 5


def test_find_hardcoded_values(tmp_path):
    py_file = tmp_path / "a.py"
    py_file.write_text("x = 150\n# 150 in comment\n", encoding="utf-8")
    results = find_hardcoded_values([str(tmp_path)])
    assert len(results) == 1
    assert results[0].startswith(str(py_file))
