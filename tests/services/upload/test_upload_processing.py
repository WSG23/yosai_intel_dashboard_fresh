from __future__ import annotations

import hashlib
import importlib.util
import sys
import types
from pathlib import Path

import pandas as pd

from yosai_intel_dashboard.src.infrastructure.validation.file_validator import (
    FileValidator,
)

stub_hashing = types.ModuleType("yosai_intel_dashboard.src.utils.hashing")
stub_hashing.hash_dataframe = lambda df: "hash"
sys.modules.setdefault(
    "yosai_intel_dashboard.src.utils.hashing", stub_hashing
)

UPLOAD_STORE_PATH = (
    Path(__file__).resolve().parents[3]
    / "yosai_intel_dashboard/src/utils/upload_store.py"
)
spec = importlib.util.spec_from_file_location("upload_store", UPLOAD_STORE_PATH)
upload_store = importlib.util.module_from_spec(spec)
spec.loader.exec_module(upload_store)  # type: ignore[arg-type]
UploadedDataStore = upload_store.UploadedDataStore


def test_size_limit_rejected():
    validator = FileValidator(max_size_mb=0.001, allowed_ext=[".csv"])
    content = b"a" * 5000
    res = validator.validate_file_upload("big.csv", content)
    assert not res["valid"]
    assert "file_too_large" in res["issues"]


def test_extension_allowlist_enforced():
    validator = FileValidator(max_size_mb=1, allowed_ext=[".csv"])
    res = validator.validate_file_upload("bad.exe", b"abc")
    assert not res["valid"]
    assert "invalid_extension" in res["issues"]


def test_atomic_move_and_checksum(tmp_path):
    store = UploadedDataStore(storage_dir=tmp_path)
    df1 = pd.DataFrame({"a": [1]})
    store.add_file("test.csv", df1)
    path = store.get_file_path("test.csv")
    with open(path, "rb") as f:
        first = hashlib.sha256(f.read()).hexdigest()

    df2 = pd.DataFrame({"a": [2]})
    store.add_file("test.csv", df2)
    with open(path, "rb") as f:
        second = hashlib.sha256(f.read()).hexdigest()

    assert first != second
    loaded = store.load_dataframe("test.csv")
    assert int(loaded.iloc[0]["a"]) == 2


def test_unicode_filename_handling(tmp_path):
    store = UploadedDataStore(storage_dir=tmp_path)
    df = pd.DataFrame({"a": [1]})
    name = "данные.csv"
    store.add_file(name, df)
    path = store.get_file_path(name)
    assert path.exists()
    loaded = store.load_dataframe(name)
    assert loaded.equals(df)
