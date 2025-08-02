import importlib.util
import sys
import types
from pathlib import Path

import pandas as pd
from tests.import_helpers import safe_import, import_optional

MODULE_PATH = (
    Path(__file__).resolve().parents[2] / "models" / "ml" / "data_processor.py"
)

# Provide lightweight stubs to avoid heavy imports during module loading
constants_mod = types.ModuleType("config.constants")
constants_mod.DEFAULT_CHUNK_SIZE = 50_000
safe_import('config.constants', constants_mod)

memory_utils_mod = types.ModuleType("utils.memory_utils")
memory_utils_mod.check_memory_limit = lambda *a, **k: None
utils_pkg = types.ModuleType("utils")
utils_pkg.memory_utils = memory_utils_mod
safe_import('utils.memory_utils', memory_utils_mod)
safe_import('utils', utils_pkg)

spec = importlib.util.spec_from_file_location("data_processor", MODULE_PATH)
dp_mod = importlib.util.module_from_spec(spec)
assert spec.loader
sys.modules[spec.name] = dp_mod
spec.loader.exec_module(dp_mod)  # type: ignore

DataProcessor = dp_mod.DataProcessor
ProcessorConfig = dp_mod.ProcessorConfig
KafkaConfig = dp_mod.KafkaConfig


def _patch_kafka(monkeypatch):
    class DummyProducer:
        instances = []

        def __init__(self, conf):
            self.conf = conf
            DummyProducer.instances.append(self)

        def flush(self):
            pass

    class DummyConsumer:
        instances = []

        def __init__(self, conf):
            self.conf = conf
            self.subscribed = None
            DummyConsumer.instances.append(self)

        def subscribe(self, topics):
            self.subscribed = topics

        def poll(self, timeout):
            return None

        def commit(self, asynchronous=True):
            pass

        def close(self):
            pass

    monkeypatch.setattr(dp_mod, "Producer", DummyProducer)
    monkeypatch.setattr(dp_mod, "Consumer", DummyConsumer)
    return DummyProducer, DummyConsumer


def _patch_processing(monkeypatch):
    monkeypatch.setattr(dp_mod, "check_memory_limit", lambda *a, **k: None)
    monkeypatch.setattr(DataProcessor, "_cleanse", lambda self, df: df)
    monkeypatch.setattr(DataProcessor, "_validate", lambda self, df: df)


def test_process_file(tmp_path, monkeypatch):
    _patch_processing(monkeypatch)
    df = pd.DataFrame({"a": range(5), "b": list("abcde")})
    csv_path = tmp_path / "data.csv"
    df.to_csv(csv_path, index=False)
    cfg = ProcessorConfig(chunk_size=2, checkpoint_path=tmp_path / "chk")
    proc = DataProcessor(cfg)
    result = proc.process_file(str(csv_path))
    assert result.reset_index(drop=True).equals(df)
    assert cfg.checkpoint_path.read_text() == "2"
    assert any(r.step == "batch_complete" for r in proc.lineage)


def test_resume_from_checkpoint(tmp_path, monkeypatch):
    _patch_processing(monkeypatch)
    df = pd.DataFrame({"a": range(5), "b": list("abcde")})
    csv_path = tmp_path / "data.csv"
    df.to_csv(csv_path, index=False)
    chk_path = tmp_path / "chk"
    chk_path.write_text("0")
    cfg = ProcessorConfig(chunk_size=2, checkpoint_path=chk_path)
    proc = DataProcessor(cfg)
    result = proc.resume_from_checkpoint(str(csv_path))
    expected = df.iloc[2:].reset_index(drop=True)
    assert result.reset_index(drop=True).equals(expected)
    assert chk_path.read_text() == "2"
    assert any(r.step == "resume_complete" for r in proc.lineage)


def test_kafka_init(monkeypatch):
    DummyProducer, DummyConsumer = _patch_kafka(monkeypatch)
    cfg = ProcessorConfig(
        kafka=KafkaConfig(brokers="b:1", topic="t", group="g"),
        checkpoint_path=Path("chk"),
    )
    proc = DataProcessor(cfg)
    assert isinstance(proc._producer, DummyProducer)
    assert isinstance(proc._consumer, DummyConsumer)
    assert proc._consumer.subscribed == [cfg.kafka.topic]
