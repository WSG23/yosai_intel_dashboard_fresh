import asyncio
import base64
import importlib.util
import json
import sys
import types
from pathlib import Path

import pandas as pd
import pytest

# Dynamically import AsyncFileProcessor to avoid heavy service deps
services_root = Path(__file__).resolve().parents[2] / "services"
services_pkg = types.ModuleType("services")
services_pkg.__path__ = [str(services_root)]
sys.modules.setdefault("services", services_pkg)

data_processing_pkg = types.ModuleType("services.data_processing")
data_processing_pkg.__path__ = [str(services_root / "data_processing")]
sys.modules.setdefault("services.data_processing", data_processing_pkg)

analytics_pkg = types.ModuleType("services.analytics")
analytics_pkg.__path__ = [str(services_root / "analytics")]
sys.modules.setdefault("services.analytics", analytics_pkg)

mapping_root = Path(__file__).resolve().parents[2] / "mapping"
mapping_pkg = types.ModuleType("mapping")
mapping_pkg.__path__ = [str(mapping_root)]
sys.modules.setdefault("mapping", mapping_pkg)

# Provide minimal config.dynamic_config for AsyncFileProcessor
config_pkg = types.ModuleType("config")
dynamic = types.SimpleNamespace(
    analytics=types.SimpleNamespace(chunk_size=2, max_memory_mb=256)
)


class DatabaseSettings:
    def __init__(self):
        self.type = "sqlite"
        self.host = ""
        self.port = 0
        self.name = ":memory:"
        self.user = ""
        self.password = ""
        self.connection_timeout = 1


config_pkg.DatabaseSettings = DatabaseSettings

config_dynamic_pkg = types.ModuleType("config.dynamic_config")
config_dynamic_pkg.dynamic_config = dynamic
sys.modules.setdefault("config", config_pkg)
sys.modules.setdefault("config.dynamic_config", config_dynamic_pkg)

protocols_pkg = types.ModuleType("core.protocols")


class FileProcessorProtocol: ...


class ConfigurationProtocol: ...


protocols_pkg.FileProcessorProtocol = FileProcessorProtocol
protocols_pkg.ConfigurationProtocol = ConfigurationProtocol
sys.modules.setdefault("core.protocols", protocols_pkg)

core_pkg = types.ModuleType("core")
config_mod = types.ModuleType("core.config")
config_mod.get_max_display_rows = lambda config=None: 5
core_pkg.config = config_mod
sys.modules.setdefault("core", core_pkg)
sys.modules.setdefault("core.config", config_mod)

perf_mod = types.ModuleType("core.performance")
perf_mod.get_performance_monitor = lambda: types.SimpleNamespace(
    throttle_if_needed=lambda: None
)
sys.modules.setdefault("core.performance", perf_mod)

perf_fp_mod = types.ModuleType("core.performance_file_processor")
perf_fp_mod.PerformanceFileProcessor = object
sys.modules.setdefault("core.performance_file_processor", perf_fp_mod)

rabbit_pkg = types.ModuleType("services.rabbitmq_client")
rabbit_pkg.RabbitMQClient = object
sys.modules.setdefault("services.rabbitmq_client", rabbit_pkg)

memory_pkg = types.ModuleType("utils.memory_utils")
memory_pkg.check_memory_limit = lambda *a, **k: None
sys.modules.setdefault("utils.memory_utils", memory_pkg)

task_queue_pkg = types.ModuleType("services.task_queue")
task_queue_pkg.create_task = lambda func: "tid"
task_queue_pkg.get_status = lambda tid: {"progress": 100, "result": None, "done": True}
task_queue_pkg.clear_task = lambda tid: None
sys.modules.setdefault("services.task_queue", task_queue_pkg)

chardet_pkg = types.ModuleType("chardet")
chardet_pkg.detect = lambda b: {"encoding": "utf-8"}
sys.modules.setdefault("chardet", chardet_pkg)

spec = importlib.util.spec_from_file_location(
    "services.data_processing.async_file_processor",
    services_root / "data_processing" / "async_file_processor.py",
)
async_module = importlib.util.module_from_spec(spec)
assert spec.loader is not None
spec.loader.exec_module(async_module)
AsyncFileProcessor = async_module.AsyncFileProcessor

spec = importlib.util.spec_from_file_location(
    "services.analytics.data_processor",
    services_root / "analytics" / "data_processor.py",
)
dp_module = importlib.util.module_from_spec(spec)
assert spec.loader is not None
spec.loader.exec_module(dp_module)
DataProcessor = dp_module.DataProcessor

spec = importlib.util.spec_from_file_location(
    "mapping.processors.column_processor",
    mapping_root / "processors" / "column_processor.py",
)
column_module = importlib.util.module_from_spec(spec)
assert spec.loader is not None
spec.loader.exec_module(column_module)
ColumnProcessor = column_module.ColumnProcessor


@pytest.mark.asyncio
async def test_async_file_processor_io(tmp_path):
    df = pd.DataFrame({"A": [1, 2], "B": [3, 4]})
    csv_path = tmp_path / "input.csv"
    df.to_csv(csv_path, index=False)
    content = "data:text/csv;base64," + base64.b64encode(csv_path.read_bytes()).decode()

    processor = AsyncFileProcessor(chunk_size=1)
    result = await processor.process_file(content, "input.csv")

    json_data = result.to_json(orient="records")
    assert json.loads(json_data)[0]["A"] == 1

    parquet_path = tmp_path / "out.parquet"
    result.to_parquet(parquet_path)
    loaded = pd.read_parquet(parquet_path)
    assert loaded.equals(result)


def test_data_processor_io(tmp_path):
    df = pd.DataFrame({"a": [1], "b": [2]})
    proc = DataProcessor()
    out = proc.process_access_events(df)

    json_data = out.to_json(orient="records")
    assert json.loads(json_data)[0]["a"] == 1

    parquet_path = tmp_path / "dp.parquet"
    out.to_parquet(parquet_path)
    loaded = pd.read_parquet(parquet_path)
    assert loaded.equals(out)


def test_mapping_processor_io(tmp_path):
    df = pd.DataFrame(
        {
            "Timestamp": ["2023-01-01T00:00:00Z"],
            "Person ID": ["p1"],
            "Device name": ["D1"],
            "Access result": ["Granted"],
        }
    )
    proc = ColumnProcessor()
    result = proc.process(df, "file.csv")

    json_str = json.dumps(result.suggestions)
    assert "timestamp" in result.data.columns
    assert json.loads(json_str)

    parquet_path = tmp_path / "mapped.parquet"
    result.data.to_parquet(parquet_path)
    loaded = pd.read_parquet(parquet_path)
    assert loaded.equals(result.data)
