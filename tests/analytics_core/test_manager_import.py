from analytics_core import create_manager


def test_create_manager() -> None:
    manager = create_manager()
    assert manager.core_service
    assert manager.ai_service
