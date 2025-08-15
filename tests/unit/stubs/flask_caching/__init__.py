class Cache:
    def __init__(self, config=None):
        self.config = config or {}

    def __getattr__(self, name):
        def decorator(*args, **kwargs):
            if name in {"memoize", "cached"}:

                def wrapper(fn):
                    return fn

                return wrapper
            return lambda *a, **kw: None

        return decorator
