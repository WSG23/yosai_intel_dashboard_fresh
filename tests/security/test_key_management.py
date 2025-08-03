"""Tests for the key management utilities."""

from pathlib import Path
from unittest.mock import Mock
import importlib.util


MODULE_PATH = (
    Path(__file__).resolve().parents[2]
    / "yosai_intel_dashboard"
    / "src"
    / "infrastructure"
    / "security"
    / "key_management.py"
)
spec = importlib.util.spec_from_file_location("key_management", MODULE_PATH)
key_management = importlib.util.module_from_spec(spec)
assert spec.loader is not None
spec.loader.exec_module(key_management)
KeyManager = key_management.KeyManager
hkdf = key_management.hkdf


def test_hkdf_length_and_uniqueness():
    base_key = b"root"
    ctx_a = b"context-a"
    ctx_b = b"context-b"

    out_a = hkdf(base_key, context=ctx_a, length=42)
    out_b = hkdf(base_key, context=ctx_b, length=42)

    assert len(out_a) == 42
    assert len(out_b) == 42
    assert out_a != out_b


def test_keymanager_rotate_invokes_writers():
    writer1 = Mock()
    writer2 = Mock()
    km = KeyManager(b"old", writers=[writer1, writer2])

    km.rotate(b"new")

    writer1.assert_called_once_with(b"new")
    writer2.assert_called_once_with(b"new")


def test_keymanager_derive_is_deterministic():
    km = KeyManager(b"master")
    first = km.derive("purpose")
    second = km.derive("purpose")

    assert first == second

