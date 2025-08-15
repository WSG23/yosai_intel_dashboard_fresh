from __future__ import annotations

from src.common.event_sourcing import Event, EventLog, EventSourcedDict


def test_record_and_rebuild_state():
    log = EventLog()
    store = EventSourcedDict(log)
    store.set("a", 1)
    store.set("b", 2)
    assert [(e.key, e.value) for e in log] == [("a", 1), ("b", 2)]

    rebuilt = EventSourcedDict(log)
    assert rebuilt.get("a") == 1
    assert rebuilt.get("b") == 2


def test_rebuild_method_replays_events():
    log = EventLog()
    store = EventSourcedDict(log)
    store.set("foo", 1)
    log.append(Event("foo", 3))
    store.rebuild()
    assert store.get("foo") == 3
