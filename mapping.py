from importlib import import_module as _im
import sys as _sys

_pkg = _im('yosai_intel_dashboard.src.mapping')

__spec__ = _pkg.__spec__
__path__ = _pkg.__path__
__package__ = _pkg.__package__
_sys.modules[__name__] = _pkg
