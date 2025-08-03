"""Graph database with indexing, caching and concurrency support.

This module provides a minimal in-memory graph database tailored for the
intel_analysis_service.  It is optimised for large sparse graphs
(>=1M nodes, >=10M edges) by combining adjacency indexing with an
LRU cache for two-hop neighbourhood queries.  A simple readers–writer
lock allows thousands of concurrent read queries while updates are
applied with exclusive access.
"""
from __future__ import annotations

from collections import defaultdict
from functools import lru_cache
import threading
import time
from typing import Dict, Iterable, Set


class RWLock:
    """A lightweight readers-writer lock.

    Multiple readers can hold the lock simultaneously, but writes are
    exclusive.  This implementation favours readers which suits the use
    case of many concurrent queries and relatively infrequent updates.
    """

    def __init__(self) -> None:
        self._read_ready = threading.Condition(threading.Lock())
        self._readers = 0

    def r_acquire(self) -> None:
        with self._read_ready:
            self._readers += 1

    def r_release(self) -> None:
        with self._read_ready:
            self._readers -= 1
            if self._readers == 0:
                self._read_ready.notify_all()

    def w_acquire(self) -> None:
        self._read_ready.acquire()
        while self._readers > 0:
            self._read_ready.wait()

    def w_release(self) -> None:
        self._read_ready.release()


class GraphDB:
    """In-memory graph database with caching for two-hop neighbourhoods."""

    def __init__(self, *, two_hop_cache_size: int = 100_000) -> None:
        # adjacency index
        self._adj: Dict[int, Set[int]] = defaultdict(set)
        self._lock = RWLock()
        self._two_hop_cache_size = two_hop_cache_size

    # ----- mutation --------------------------------------------------
    def add_edge(self, src: int, dst: int) -> float:
        """Add an undirected edge and return update latency in ms.

        The cache is cleared to keep neighbourhood queries consistent.
        """
        start = time.perf_counter()
        self._lock.w_acquire()
        try:
            self._adj[src].add(dst)
            self._adj[dst].add(src)
            self._compute_two_hop.cache_clear()
        finally:
            self._lock.w_release()
        return (time.perf_counter() - start) * 1000

    # ----- queries ---------------------------------------------------
    def neighbours(self, node: int) -> Set[int]:
        self._lock.r_acquire()
        try:
            return set(self._adj.get(node, set()))
        finally:
            self._lock.r_release()

    def two_hop_neighbours(self, node: int) -> Set[int]:
        self._lock.r_acquire()
        try:
            return self._compute_two_hop(node)
        finally:
            self._lock.r_release()

    @lru_cache(maxsize=100_000)
    def _compute_two_hop(self, node: int) -> Set[int]:
        first = self._adj.get(node, set())
        second: Set[int] = set()
        for neighbour in first:
            second.update(self._adj.get(neighbour, set()))
        second.discard(node)
        return second

    # ----- utilities -------------------------------------------------
    def bulk_load(self, edges: Iterable[tuple[int, int]]) -> None:
        """Load many edges efficiently."""
        self._lock.w_acquire()
        try:
            for src, dst in edges:
                self._adj[src].add(dst)
                self._adj[dst].add(src)
            self._compute_two_hop.cache_clear()
        finally:
            self._lock.w_release()
