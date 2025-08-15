from __future__ import annotations

import importlib.util
from pathlib import Path

import pytest

spec = importlib.util.spec_from_file_location(
    "unicode_processor",
    Path(__file__).resolve().parents[1]
    / "yosai_intel_dashboard/src/infrastructure/config/unicode_processor.py",
)
unicode_processor = importlib.util.module_from_spec(spec)
assert spec.loader is not None
spec.loader.exec_module(unicode_processor)  # type: ignore[attr-defined]
encode_query = unicode_processor.encode_query
encode_params = unicode_processor.encode_params


def test_encode_query_surrogate_pair():
    text = chr(0xD83D) + chr(0xDC36)  # dog face
    assert encode_query(text) == "🐶"


def test_encode_query_bytes():
    q = b"SELECT \xf0\x9f\x90\xb6"
    assert encode_query(q) == "SELECT 🐶"


def test_encode_params_mixed_encodings():
    params = ["ok", b"\xf0\x9f\x92\xa9", {"x": "bad" + chr(0xD800)}]
    result = encode_params(params)
    assert result[0] == "ok"
    assert result[1] == "💩"
    assert result[2]["x"] == "bad"
