from __future__ import annotations

"""Helpers for resolving database shards.

This module provides a small utility for dividing large tables across
multiple database shards.  The :class:`ShardResolver` maps a table name and a
record key to the connection string for the shard that should contain the
record.  The hashing strategy is intentionally simple – a stable hash of the
key modulo the number of configured shards – but the class is designed to be
extensible if more sophisticated routing is required in the future.
"""

from dataclasses import dataclass
from typing import Dict, Optional, Sequence, Union


@dataclass
class ShardResolver:
    """Resolve which shard should service a given table/key combination."""

    shard_map: Dict[str, Sequence[str]]

    def resolve(self, table: str, key: Union[str, int]) -> Optional[str]:
        """Return the shard connection string for ``table`` and ``key``.

        Parameters
        ----------
        table:
            Name of the table being accessed.
        key:
            Identifier for the record.  Any hashable value may be used.

        Returns
        -------
        Optional[str]
            The connection string for the selected shard or ``None`` if the
            table is not sharded.
        """

        shards = self.shard_map.get(table)
        if not shards:
            return None
        index = hash(key) % len(shards)
        return shards[index]


__all__ = ["ShardResolver"]
