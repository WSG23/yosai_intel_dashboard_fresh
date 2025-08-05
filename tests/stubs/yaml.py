from __future__ import annotations


class SafeLoader:
    @classmethod
    def add_constructor(cls, *a, **k):
        pass


class Node:
    pass


def safe_load(data):
    return {}


def load(*a, **k):
    return {}


def dump(*a, **k):
    return ""


__all__ = ["SafeLoader", "Node", "safe_load", "load", "dump"]
