from __future__ import annotations

"""Expose upload analytics processing helpers.

Historically the project relied on runtime patch scripts to attach analytics
helpers to :class:`UploadAnalyticsProcessor`.  The processor now ships with a
fully fledged implementation and can be imported directly from this module
without any additional patching.
"""

from yosai_intel_dashboard.src.utils.upload_store import (
    UploadedDataStore,
    get_uploaded_data_store,
)

from .upload.upload_processing import UploadAnalyticsProcessor

__all__ = [
    "UploadAnalyticsProcessor",
    "UploadedDataStore",
    "get_uploaded_data_store",
]
