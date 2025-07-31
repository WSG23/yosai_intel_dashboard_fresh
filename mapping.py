from importlib import import_module as _im
import sys as _sys
_sys.modules[__name__] = _im('yosai_intel_dashboard.src.mapping')
