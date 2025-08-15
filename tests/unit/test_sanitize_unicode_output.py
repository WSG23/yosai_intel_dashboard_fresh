from __future__ import annotations

import builtins
import sys
import types

import pandas as pd


def _import_optional(name, fallback=None):
    return fallback


builtins.import_optional = _import_optional

core_config_stub = types.ModuleType("yosai_intel_dashboard.src.core.config")
core_config_stub.get_max_display_rows = lambda config=None: 100
sys.modules.setdefault("yosai_intel_dashboard.src.core.config", core_config_stub)

from yosai_intel_dashboard.src.file_processing.utils import (  # noqa: E402
    sanitize_dataframe_unicode,
)


def test_sanitize_dataframe_unicode_stream_equivalence():
    df = pd.DataFrame({"text": ["bad\ud83d\ude00", "ok"]})
    expected = pd.DataFrame({"text": ["bad😀", "ok"]})

    direct = sanitize_dataframe_unicode(df, chunk_size=1, stream=False)
    streamed = pd.concat(
        list(sanitize_dataframe_unicode(df, chunk_size=1, stream=True))
    )

    pd.testing.assert_frame_equal(direct, expected)
    pd.testing.assert_frame_equal(streamed, expected)
