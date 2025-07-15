import pandas as pd

from mapping.storage.base import MemoryStorage
from mapping.processors.column_processor import ColumnProcessor
from mapping.processors.device_processor import DeviceProcessor
from mapping.processors.ai_processor import AIColumnMapperAdapter


class DummyAdapter:
    def get_ai_column_suggestions(self, df, filename):
        return {c: {} for c in df.columns}

    def save_verified_mappings(self, filename, mapping, metadata):
        return True


def test_memory_storage_roundtrip():
    store = MemoryStorage()
    data = {"a": 1}
    store.save(data)
    assert store.load() == data


def test_column_and_device_processing():
    df = pd.DataFrame({"Device name": ["Door1"], "Person ID": ["p"]})
    column_proc = ColumnProcessor(AIColumnMapperAdapter(DummyAdapter()))
    result = column_proc.process(df, "file.csv")
    assert not result.data.empty
    device_proc = DeviceProcessor()
    devices = device_proc.process(result.data)
    assert devices.metadata["devices"] == ["Door1"]
