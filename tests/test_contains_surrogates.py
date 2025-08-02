import pytest

from yosai_intel_dashboard.src.core.unicode import contains_surrogates


def test_contains_surrogates_detects_unpaired_high():
    assert contains_surrogates("A\ud800B")


def test_contains_surrogates_detects_unpaired_low():
    assert contains_surrogates("\udc00")


def test_contains_surrogates_ignores_valid_pair():
    assert not contains_surrogates("\ud800\udc00")
