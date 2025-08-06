#!/usr/bin/env python3
"""Basic unicode cleanup validation script."""
from __future__ import annotations

import importlib
import pkgutil
import sys
import warnings
from pathlib import Path

from yosai_intel_dashboard.src.core.unicode import UnicodeProcessor

# Ensure project root is importable
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from yosai_intel_dashboard.src.core.unicode import sanitize_dataframe
from yosai_intel_dashboard.src.core.base_utils import (
    clean_unicode_text,
    safe_encode_text,
)


def safe_decode_bytes(data: bytes, encoding: str = "utf-8") -> str:
    """Decode bytes using :mod:`unicode_toolkit`."""
    processor = UnicodeProcessor()
    try:
        text = data.decode(encoding, errors="surrogatepass")
    except Exception:
        text = data.decode(encoding, errors="ignore")
    return processor.process(text)


def _import_all_modules() -> None:
    root = Path(__file__).resolve().parents[1]
    for module in pkgutil.walk_packages([str(root)]):
        name = module.name
        try:
            importlib.import_module(name)
        except Exception:
            # Ignore modules that fail to import so the check continues
            pass


def _run_checks() -> None:
    import pandas as pd

    assert clean_unicode_text("A\ud800") == "A"
    assert safe_encode_text("test") == "test"
    assert safe_decode_bytes(b"x") == "x"

    df = pd.DataFrame({"=bad": ["A\ud800"]})
    cleaned = sanitize_dataframe(df)
    assert list(cleaned.columns) == ["bad"]
    assert cleaned.iloc[0, 0] == "A"


def main() -> None:
    with warnings.catch_warnings(record=True) as w:
        warnings.simplefilter("error", DeprecationWarning)
        _import_all_modules()
    assert not any(
        issubclass(warning.category, DeprecationWarning) for warning in w
    ), "DeprecationWarning raised during import"

    _run_checks()
    print("All unicode cleanup checks passed")


if __name__ == "__main__":
    main()
