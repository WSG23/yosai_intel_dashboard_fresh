from types import SimpleNamespace


class Dummy:
    max_display_rows = 100


def get_analytics_config():
    return Dummy()


def get_config():
    return SimpleNamespace(
        get_app_config=lambda: SimpleNamespace(
            environment="development", title="title"
        ),
        get_security_config=lambda: SimpleNamespace(csrf_enabled=False),
        get_analytics_config=get_analytics_config,
    )
