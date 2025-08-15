from __future__ import annotations

class StatefulServiceV1:
    """First version of a simple stateful counter."""

    def __init__(self, store: dict[str, int]):
        self.store = store

    def increment(self) -> int:
        self.store["value"] = self.store.get("value", 0) + 1
        return self.store["value"]


class StatefulServiceV2(StatefulServiceV1):
    """Second version sharing the same underlying store."""

    # This version adds a no-op method representing a new feature
    def ping(self) -> bool:  # pragma: no cover - trivial
        return True


def test_simultaneous_versions_share_state():
    store: dict[str, int] = {}
    v1 = StatefulServiceV1(store)
    v2 = StatefulServiceV2(store)

    assert v1.increment() == 1
    assert v2.increment() == 2
    assert v1.increment() == 3
    assert v2.increment() == 4
