#!/usr/bin/env python3
"""Test file processor without UI dependencies"""
import io

import pandas as pd
import pytest

from yosai_intel_dashboard.src.services.data_processing.file_processor import (
    UnicodeFileProcessor,
    create_file_preview,
    process_uploaded_file,
)


def test_unicode_processor_isolation():
    """Test Unicode processor works independently"""
    processor = UnicodeFileProcessor()

    # Test surrogate handling
    bad_content = b"\xed\xa0\x80\xed\xb0\x80"  # Surrogate pair
    result = processor.safe_decode_content(bad_content)
    assert isinstance(result, str)

    # Test DataFrame sanitization
    df = pd.DataFrame({"col": ["normal", "bad\ud800\udc00text"]})
    clean_df = processor.sanitize_dataframe_unicode(df)
    assert clean_df["col"].iloc[1] == "bad\ud800\udc00text"


def test_preview_without_ui():
    """Test preview creation returns data structure, not UI"""
    df = pd.DataFrame({"A": [1, 2], "B": ["x", "y"]})
    preview = create_file_preview(df)

    assert "preview_data" in preview
    assert "columns" in preview
    assert isinstance(preview["preview_data"], list)
    assert len(preview["columns"]) == 2
