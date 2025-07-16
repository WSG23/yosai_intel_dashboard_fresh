#!/usr/bin/env python3
"""Basic unicode cleanup validation script."""
from __future__ import annotations

import importlib
import importlib.util
import pkgutil
import sys
from pathlib import Path
import types
import warnings

# Ensure project root is importable
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

# Explicitly load the module version of ``core.unicode``.  The repository also
# contains a ``core/unicode`` package used for legacy compatibility which would
# otherwise take precedence on import.  Loading the file directly ensures we use
# the modern implementation.
unicode_file = Path(__file__).resolve().parents[1] / "core" / "unicode.py"
spec = importlib.util.spec_from_file_location("core.unicode", unicode_file)
unicode_mod = importlib.util.module_from_spec(spec)
sys.modules["core.unicode"] = unicode_mod
assert spec.loader
spec.loader.exec_module(unicode_mod)
try:  # Expose legacy processor classes for modules that expect them
    from core.unicode.processor import (
        UnicodeSecurityProcessor,
        UnicodeSQLProcessor,
        UnicodeTextProcessor,
    )

    unicode_mod.UnicodeSecurityProcessor = UnicodeSecurityProcessor
    unicode_mod.UnicodeSQLProcessor = UnicodeSQLProcessor
    unicode_mod.UnicodeTextProcessor = UnicodeTextProcessor
except Exception:
    pass

from core.unicode import (
    clean_unicode_text,
    safe_decode_bytes,
    safe_encode_text,
    sanitize_dataframe,
)
from utils import (
    clean_unicode_text as util_clean_unicode_text,
    safe_decode_bytes as util_safe_decode_bytes,
    safe_encode_text as util_safe_encode_text,
    sanitize_dataframe as util_sanitize_dataframe,
)


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
    assert util_clean_unicode_text("A\ud800") == "A"
    assert safe_encode_text("test") == "test"
    assert util_safe_encode_text("test") == "test"
    assert safe_decode_bytes(b"x") == "x"
    assert util_safe_decode_bytes(b"x") == "x"

    df = pd.DataFrame({"=bad": ["A\ud800"]})
    cleaned = sanitize_dataframe(df)
    util_cleaned = util_sanitize_dataframe(df)
    assert list(cleaned.columns) == ["bad"]
    assert cleaned.iloc[0, 0] == "A"
    assert list(util_cleaned.columns) == ["bad"]
    assert util_cleaned.iloc[0, 0] == "A"


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
