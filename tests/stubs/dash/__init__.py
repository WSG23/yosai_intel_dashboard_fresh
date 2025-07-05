class Dash:
    def callback(self, *args, **kwargs):
        def decorator(func):
            return func
        return decorator

from . import html
__all__ = ["Dash", "html"]
