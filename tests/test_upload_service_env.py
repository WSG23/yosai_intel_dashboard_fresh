import base64
import importlib

from tests.fake_configuration import FakeConfiguration
from services.data_processing import file_processor as upload_module


def test_env_max_upload_limit(monkeypatch):
    cfg = FakeConfiguration()
    monkeypatch.setattr(cfg.security, "max_upload_mb", 1)

    max_bytes = cfg.security.max_upload_mb * 1024 * 1024
    data = base64.b64encode(b"A" * (max_bytes + 1)).decode()
    contents = f"data:text/csv;base64,{data}"
    result = upload_module.process_uploaded_file(contents, "big.csv", config=cfg)
    assert result["success"] is False
