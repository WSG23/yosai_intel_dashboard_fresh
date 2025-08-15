from yosai_intel_dashboard.src.services.query_optimizer import (
    end_request_tracking,
    start_request_tracking,
    track_query,
)
from yosai_intel_dashboard.src.core.performance import profiler


def test_n_plus_one_detection_records_queries():
    profiler.n_plus_one_queries.clear()
    start_request_tracking()
    track_query("SELECT * FROM users WHERE id=1")
    track_query("SELECT * FROM users WHERE id=2")
    end_request_tracking("/users")

    data = profiler.get_n_plus_one_queries()
    assert "/users" in data
    assert data["/users"][0]["stacks"]
    assert data["/users"][0]["query"].startswith("SELECT * FROM users")

