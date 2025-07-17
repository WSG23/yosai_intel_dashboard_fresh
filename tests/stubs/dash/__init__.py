from . import html
from . import dcc
from . import dependencies
from . import _callback

# Re-export commonly used classes for convenience
Input = dependencies.Input
Output = dependencies.Output
State = dependencies.State


class Dash:
    def callback(self, *args, **kwargs):
        def decorator(func):
            return func

        return decorator


class _SimpleComp:
    def __init__(self, *a, **k):
        pass


no_update = _callback.NoUpdate()
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
]
