from __future__ import annotations

import hashlib
import io
import sys
import types
from pathlib import Path

import pytest

stub_hashing = types.ModuleType("yosai_intel_dashboard.src.utils.hashing")
stub_hashing.hash_dataframe = lambda df: "hash"
sys.modules.setdefault("yosai_intel_dashboard.src.utils.hashing", stub_hashing)

stub_preview = types.ModuleType("yosai_intel_dashboard.src.utils.preview_utils")
stub_preview.serialize_dataframe_preview = lambda df: ""
sys.modules.setdefault("yosai_intel_dashboard.src.utils.preview_utils", stub_preview)

stub_cfg_mgr = types.ModuleType(
    "yosai_intel_dashboard.src.infrastructure.config.config_manager"
)
stub_cfg_mgr.create_config_manager = lambda *a, **k: None
sys.modules.setdefault(
    "yosai_intel_dashboard.src.infrastructure.config.config_manager", stub_cfg_mgr
)

stub_store = types.ModuleType("yosai_intel_dashboard.src.utils.upload_store")
stub_store.get_uploaded_data_store = lambda *a, **k: None
sys.modules.setdefault("yosai_intel_dashboard.src.utils.upload_store", stub_store)

from yosai_intel_dashboard.src.services.upload.upload_processing import stream_upload


def test_size_limit_rejected(tmp_path):
    src = io.BytesIO(b"a" * 10)
    with pytest.raises(ValueError):
        stream_upload(src, tmp_path, "big.csv", max_bytes=5)


def test_extension_allowlist_enforced(tmp_path):
    src = io.BytesIO(b"data")
    with pytest.raises(ValueError):
        stream_upload(src, tmp_path, "bad.exe", allowed_extensions={".csv"})


def test_atomic_move_and_checksum(tmp_path):
    data1 = b"first"
    res1 = stream_upload(io.BytesIO(data1), tmp_path, "file.csv")
    dest = Path(tmp_path) / "file.csv"
    assert dest.exists()
    assert res1.sha256 == hashlib.sha256(data1).hexdigest()

    data2 = b"second"
    res2 = stream_upload(io.BytesIO(data2), tmp_path, "file.csv")
    assert res2.sha256 == hashlib.sha256(data2).hexdigest()
    with open(dest, "rb") as f:
        assert f.read() == data2


def test_unicode_filename_handling(tmp_path):
    name = "данные.csv"
    stream_upload(io.BytesIO(b"data"), tmp_path, name)
    assert (Path(tmp_path) / name).exists()
