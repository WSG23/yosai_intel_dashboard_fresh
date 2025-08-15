from __future__ import annotations

import json

import pytest

from yosai_intel_dashboard.src.services.flag_evaluator import FlagEvaluator


class FakeRedis:
    def __init__(self):
        self.store = {}

    def set(self, key, value):
        self.store[key] = value

    def get(self, key):
        return self.store.get(key)


def test_dependency_order_and_evaluation():
    flags = {
        "b": {"value": True},
        "a": {"value": True, "dependencies": ["b"], "fallback": False},
    }
    r = FakeRedis()
    r.set("feature_flags", json.dumps(flags))
    evaluator = FlagEvaluator(r)
    assert evaluator.order == ["b", "a"]
    assert evaluator.evaluate("a") is True


def test_fallback_when_dependency_off():
    flags = {
        "b": {"value": False},
        "a": {"value": True, "dependencies": ["b"], "fallback": False},
    }
    r = FakeRedis()
    r.set("feature_flags", json.dumps(flags))
    evaluator = FlagEvaluator(r)
    assert evaluator.evaluate("a") is False


def test_cycle_detection():
    flags = {
        "a": {"value": True, "dependencies": ["b"]},
        "b": {"value": True, "dependencies": ["a"]},
    }
    r = FakeRedis()
    r.set("feature_flags", json.dumps(flags))
    with pytest.raises(ValueError):
        FlagEvaluator(r)
