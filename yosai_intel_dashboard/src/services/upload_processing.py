from __future__ import annotations

"""Expose upload analytics processing helpers.

Historically the project relied on runtime patch scripts to attach analytics
helpers to :class:`UploadAnalyticsProcessor`.  The processor now ships with a
fully fledged implementation and can be imported directly from this module
without any additional patching.
"""

from .upload.upload_processing import (
    UploadAnalyticsProcessor,
    clean_uploaded_dataframe,
    get_analytics_from_uploaded_data,
    summarize_dataframe,
)

__all__ = [
    "UploadAnalyticsProcessor",
    "get_analytics_from_uploaded_data",
    "clean_uploaded_dataframe",
    "summarize_dataframe",
]
