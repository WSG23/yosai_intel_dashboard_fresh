from __future__ import annotations

from yosai_intel_dashboard.src.database.shard_resolver import ShardResolver


def test_resolver_returns_consistent_shard():
    resolver = ShardResolver({"big_table": ["db1", "db2", "db3"]})
    shard_a = resolver.resolve("big_table", "user_a")
    shard_b = resolver.resolve("big_table", "user_a")
    assert shard_a == shard_b
    assert shard_a in {"db1", "db2", "db3"}


def test_resolver_handles_unsharded_table():
    resolver = ShardResolver({"big_table": ["db1", "db2"]})
    assert resolver.resolve("other_table", 1) is None
