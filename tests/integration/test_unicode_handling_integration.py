import pandas as pd

import yosai_intel_dashboard.src.core as core.unicode
import yosai_intel_dashboard.src.core as handler
from yosai_intel_dashboard.src.core.unicode import UnicodeProcessor, sanitize_dataframe


def test_unicode_handler_centralization():
    text = "A" + chr(0xD800) + "B"
    cleaned = handler.UnicodeProcessor.clean_surrogate_chars(text)
    assert cleaned == "AB"

    assert UnicodeProcessor.clean_surrogate_chars(text) == cleaned

    df = pd.DataFrame({"c" + chr(0xD800): ["x" + chr(0xDC00)]})
    cleaned_df = sanitize_dataframe(df)
    assert list(cleaned_df.columns) == ["c"]
    assert cleaned_df.iloc[0, 0] == "x"

    from yosai_intel_dashboard.src.infrastructure.security.unicode_security_handler import (
        UnicodeSecurityHandler,
    )

    assert UnicodeSecurityHandler.sanitize_unicode_input(text) == cleaned
    sec_df = UnicodeSecurityHandler.sanitize_dataframe(df)
    assert list(sec_df.columns) == ["c"]
    assert sec_df.iloc[0, 0] == "x"
