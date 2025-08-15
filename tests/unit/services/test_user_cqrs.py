from yosai_intel_dashboard.src.services.user import (
    UserCommand,
    UserCommandService,
    UserQuery,
    UserQueryService,
)


def test_user_command_and_query_services() -> None:
    store: dict[str, str] = {}
    command_service = UserCommandService(store)
    query_service = UserQueryService(store)

    command = UserCommand(user_id="u1", name="Alice")
    command_service.create_user(command)

    query = UserQuery(user_id="u1")
    result = query_service.get_user(query)
    assert result == "Alice"
