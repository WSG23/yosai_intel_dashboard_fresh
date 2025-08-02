from yosai_intel_dashboard.src.core.navigation.enterprise_navigation_manager import (
    EnterpriseNavigationManager,
    NavigationLoopError,
)


def test_navigation_loop_detection():
    manager = EnterpriseNavigationManager(loop_threshold=3)
    manager.record_navigation("A")
    manager.record_navigation("A")

    try:
        manager.record_navigation("A")
    except NavigationLoopError:
        loop_detected = True
    else:
        loop_detected = False

    assert loop_detected
    assert manager.get_history()[-1] == "A"
