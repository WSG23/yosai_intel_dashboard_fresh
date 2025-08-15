from yosai_intel_dashboard.src.core.state import CentralizedStateManager


def test_state_updates_and_subscribe():
    manager = CentralizedStateManager({"count": 0})
    seen = []

    def listener(state, action):
        seen.append((state["count"], action["type"]))

    manager.subscribe(listener)
    manager.dispatch("inc", {"count": 1})
    manager.dispatch("inc", {"count": 2})

    assert manager.get_state()["count"] == 2
    assert seen == [(1, "inc"), (2, "inc")]
