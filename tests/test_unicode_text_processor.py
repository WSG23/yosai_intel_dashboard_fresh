import pytest

from yosai_intel_dashboard.src.core.unicode import object_count


def test_object_count_basic():
    items = ["a", "b", "b", "c", "c", "c"]
    assert object_count(items) == 2


def test_object_count_ignores_non_strings():
    items = ["x", 1, "x", 2, 3, "y"]
    assert object_count(items) == 1


def test_object_count_no_duplicates():
    assert object_count(["a", "b", "c"]) == 0
