from __future__ import annotations

import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent / "stubs"))
os.environ.setdefault("LIGHTWEIGHT_SERVICES", "1")

from src.services.upload.stream_upload import stream_upload
from src.services.upload.unicode import (
    normalize_text,
    safe_decode_bytes,
    safe_encode_text,
)


class DummyStore:
    def __init__(self) -> None:
        self.files = {}

    def add_file(self, filename: str, data) -> None:
        self.files[filename] = data

    def get_filenames(self):
        return list(self.files.keys())


def test_normalize_text_decodes_surrogate_pair():
    assert normalize_text("\ud800\udc00") == "\U00010000"


def test_safe_decode_bytes_handles_surrogate_pair():
    pair_bytes = b"\xed\xa0\x80\xed\xb0\x80"
    assert safe_decode_bytes(pair_bytes) == "\U00010000"


def test_safe_encode_text_handles_surrogate_pair_bytes():
    pair_bytes = b"\xed\xa0\x80\xed\xb0\x80"
    assert safe_encode_text(pair_bytes) == "\U00010000"


def test_stream_upload_normalizes_filename_with_surrogates():
    store = DummyStore()
    filename = "\ud800\udc00.csv"
    stream_upload(store, filename, object())
    assert "\U00010000.csv" in store.get_filenames()
