"""Compliance services exported under the ``services.compliance`` namespace."""

from pkgutil import extend_path
import sys

# Allow other packages to extend this namespace
__path__ = extend_path(__path__, __name__)

# Register this package as ``services.compliance`` so imports under that path work
sys.modules.setdefault("services.compliance", sys.modules[__name__])

__all__ = []
