from . import _callback, dcc, dependencies, html

# Re-export commonly used classes for convenience
Input = dependencies.Input
Output = dependencies.Output
State = dependencies.State
import types

dash_table = types.ModuleType("dash_table")


class Dash:
    def __init__(self, *args, **kwargs):
        pass

    def callback(self, *args, **kwargs):
        def decorator(func):
            return func

        return decorator


class _SimpleComp:
    def __init__(self, *a, **k):
        pass


no_update = _callback.NoUpdate()


def register_page(name=None, path="/", app=None, **kwargs):
    """Stub for `dash.register_page` used in tests."""
    return None


__version__ = "0.0.0"
page_container = _SimpleComp()


__all__ = [
    "Dash",
    "html",
    "dcc",
    "dependencies",
    "_callback",
    "Input",
    "Output",
    "State",
    "no_update",
    "register_page",
    "dash_table",
]
