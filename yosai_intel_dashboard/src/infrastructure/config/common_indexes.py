from __future__ import annotations

from typing import Mapping, Sequence, Tuple

# Mapping of table names to sequences of column groups that should be indexed.
# Each column group is a tuple of column names representing a single index.
COMMON_INDEXES: Mapping[str, Sequence[Tuple[str, ...]]] = {
    # Example entries. Extend as needed for application tables.
    "events": [("user_id",), ("facility_id", "created_at")],
}

__all__ = ["COMMON_INDEXES"]
