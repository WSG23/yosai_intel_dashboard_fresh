from importlib import import_module
import sys

_module = import_module('.src.export', __name__)
sys.modules[__name__] = _module
