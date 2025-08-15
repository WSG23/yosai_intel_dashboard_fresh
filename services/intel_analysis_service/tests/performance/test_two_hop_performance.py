"""Performance benchmarks for :mod:`graph_db`.

The tests are light‑weight but validate that the indexing and caching
strategies provide the expected performance guarantees for two‑hop
neighbourhood queries and real‑time updates.
"""

import time
from concurrent.futures import ThreadPoolExecutor
import pathlib
import sys

# ensure the graph_db module is importable
SERVICE_DIR = (
    pathlib.Path(__file__).resolve().parents[4]
    / "yosai_intel_dashboard"
    / "src"
    / "services"
    / "intel_analysis_service"
)
sys.path.append(str(SERVICE_DIR.resolve()))

from graph_db import GraphDB  # noqa: E402


def _build_graph() -> GraphDB:
    g = GraphDB()
    # create a fan-out graph to exercise two-hop logic
    for i in range(1, 5001):
        g.add_edge(0, i)
        g.add_edge(i, i + 5000)
    return g


def test_two_hop_under_one_second() -> None:
    g = _build_graph()
    start = time.perf_counter()
    neighbours = g.two_hop_neighbours(0)
    duration = time.perf_counter() - start
    assert duration < 1.0
    # basic sanity – should discover second hop nodes
    assert len(neighbours) >= 5000


def test_update_latency_under_100ms() -> None:
    g = GraphDB()
    latency = g.add_edge(1, 2)
    assert latency < 100


def test_handles_many_concurrent_queries() -> None:
    g = _build_graph()
    with ThreadPoolExecutor(max_workers=1000) as executor:
        futures = [executor.submit(g.two_hop_neighbours, 0) for _ in range(1000)]
        assert all(f.result() for f in futures)
