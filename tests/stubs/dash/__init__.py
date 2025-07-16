class Dash:
    def callback(self, *args, **kwargs):
        def decorator(func):
            return func

        return decorator


class _SimpleComp:
    def __init__(self, *a, **k):
        pass


from . import html
from . import dcc
from . import dependencies
from . import _callback

no_update = _callback.NoUpdate()
__version__ = "0.0.0"


__all__ = [
    "Dash",
    "html",
    "dcc",
    "dependencies",
    "_callback",
]
