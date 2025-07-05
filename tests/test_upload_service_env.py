import base64
import importlib

from config import dynamic_config as dyn_module
from services.data_processing import process_file


def test_env_max_upload_limit(monkeypatch):
    monkeypatch.setenv("MAX_UPLOAD_MB", "1")
    importlib.reload(dyn_module)

    max_bytes = dyn_module.dynamic_config.security.max_upload_mb * 1024 * 1024
    data = base64.b64encode(b"A" * (max_bytes + 1)).decode()
    contents = f"data:text/csv;base64,{data}"
    result = process_file(contents, "big.csv")
    assert result["success"] is False

    monkeypatch.delenv("MAX_UPLOAD_MB", raising=False)
    importlib.reload(dyn_module)
