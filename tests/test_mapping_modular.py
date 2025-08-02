import pandas as pd

from yosai_intel_dashboard.src.infrastructure.di.service_container import ServiceContainer
from yosai_intel_dashboard.src.services.mapping.models import MappingModel
from yosai_intel_dashboard.src.services.mapping.processors.ai_processor import AIColumnMapperAdapter
from yosai_intel_dashboard.src.services.mapping.processors.column_processor import ColumnProcessor
from yosai_intel_dashboard.src.services.mapping.processors.device_processor import DeviceProcessor
from yosai_intel_dashboard.src.services.mapping.storage.base import MemoryStorage


class DummyAdapter:
    def get_ai_column_suggestions(self, df, filename):
        return {c: {} for c in df.columns}

    def save_verified_mappings(self, filename, mapping, metadata):
        return True


class DummyModel:
    def __init__(self):
        self.called = False

    def suggest(self, df, filename):
        self.called = True
        return {c: {"field": c.lower(), "confidence": 1.0} for c in df.columns}


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


def test_column_processor_uses_registered_model():
    df = pd.DataFrame({"A": [1], "B": [2]})
    container = ServiceContainer()
    model = DummyModel()
    container.register_singleton("mapping_model:dummy", model, protocol=MappingModel)
    proc = ColumnProcessor(
        ai_adapter=AIColumnMapperAdapter(DummyAdapter(), container=container),
        container=container,
    )
    result = proc.process(df, "file.csv", model_key="dummy")
    assert model.called
    assert result.suggestions["A"]["field"] == "a"
