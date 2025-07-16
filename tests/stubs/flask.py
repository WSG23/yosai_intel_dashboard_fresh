class Flask:
    def __init__(self, *args, **kwargs):
        self.config = {}
        self.teardown_funcs = []

    def teardown_appcontext(self, func):
        self.teardown_funcs.append(func)
        return func


# Minimal stubs for Flask globals used in tests
class _Request:
    """Simple request stub."""

    def __init__(self) -> None:
        self.args = {}
        self.form = {}


request = _Request()


class Response:
    def __init__(self, data: str = "", status: int = 200) -> None:
        self.data = data
        self.status_code = status

    def set_data(self, data: str) -> None:
        self.data = data

    def get_data(self, as_text: bool = False):
        return self.data if as_text else self.data.encode()


def url_for(endpoint: str, **values: str) -> str:
    """Return a fake URL for the given endpoint."""
    value_str = "&".join(f"{k}={v}" for k, v in values.items())
    return f"/{endpoint}?{value_str}" if value_str else f"/{endpoint}"


session = {}
