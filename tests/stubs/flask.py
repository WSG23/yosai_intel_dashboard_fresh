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


def url_for(endpoint: str, **values: str) -> str:
    """Return a fake URL for the given endpoint."""
    value_str = "&".join(f"{k}={v}" for k, v in values.items())
    return f"/{endpoint}?{value_str}" if value_str else f"/{endpoint}"

session = {}
