from importlib import import_module
def load_callable(spec: str):
    mod, attr = spec.split(":", 1)
    return getattr(import_module(mod), attr)
