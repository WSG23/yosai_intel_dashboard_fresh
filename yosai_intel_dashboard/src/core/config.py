from __future__ import annotations

"""Compatibility layer for configuration helpers.

Historically, helper functions such as ``get_max_display_rows`` lived in this
module. They now reside in :mod:`yosai_intel_dashboard.src.core.config_helpers`
to avoid circular import issues. The functions are re-exported here for
backwards compatibility.
"""

from yosai_intel_dashboard.src.core.config_helpers import (
    get_db_pool_size,
    get_max_display_rows,
    get_max_parallel_uploads,
    get_max_upload_size_bytes,
    get_validator_rules,
    validate_large_file_support,
)


__all__ = [
    "get_max_parallel_uploads",
    "get_validator_rules",
    "get_max_upload_size_bytes",
    "validate_large_file_support",
    "get_db_pool_size",
    "get_max_display_rows",
]

