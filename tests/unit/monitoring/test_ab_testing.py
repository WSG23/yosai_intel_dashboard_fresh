import os

os.environ.setdefault("LIGHTWEIGHT_SERVICES", "1")

from yosai_intel_dashboard.src.infrastructure.monitoring.ab_testing import ABTest


def test_traffic_split():
    ab = ABTest({"A": 0.5, "B": 0.5})
    counts = {"A": 0, "B": 0}
    for user in range(1000):
        counts[ab.assign(user)] += 1
    assert 400 < counts["A"] < 600
    assert 400 < counts["B"] < 600


def test_metric_logging():
    ab = ABTest({"A": 1, "B": 1})
    ab.log_metric("A", 1)
    ab.log_metric("A", 0)
    ab.log_metric("B", 1)
    assert ab.metrics["A"] == [1, 0]
    assert ab.metrics["B"] == [1]


def test_chi_square_significance():
    ab = ABTest({"A": 1, "B": 1}, metric_type="binary")
    for _ in range(20):
        ab.log_metric("A", 1)
    for _ in range(80):
        ab.log_metric("A", 0)
    for _ in range(40):
        ab.log_metric("B", 1)
    for _ in range(60):
        ab.log_metric("B", 0)
    assert ab.evaluate() == "B"


def test_ttest_significance():
    ab = ABTest({"A": 1, "B": 1}, metric_type="continuous")
    for i in range(30):
        ab.log_metric("A", float(i))
        ab.log_metric("B", float(i + 10))
    assert ab.evaluate() == "B"
