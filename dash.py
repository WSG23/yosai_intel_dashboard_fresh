"""
Shim module to provide dash.no_update in environments
where dash.no_update is missing.
"""

import importlib

# Import the real dash package
_real_dash = importlib.import_module('dash')

try:
    no_update = getattr(_real_dash, 'no_update')
except AttributeError:
    no_update = None  # sentinel if dash.no_update is missing

__all__ = list(getattr(_real_dash, '__all__', [n for n in dir(_real_dash) if not n.startswith('_')]))
if 'no_update' not in __all__:
    __all__.append('no_update')


def __getattr__(name):
    return getattr(_real_dash, name)
