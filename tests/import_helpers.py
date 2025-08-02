from __future__ import annotations

import sys
from types import ModuleType
from typing import Any

from optional_dependencies import import_optional as _import_optional


def safe_import(name: str, stub: ModuleType | Any) -> ModuleType | Any:
    """Import ``name`` or register ``stub`` in ``sys.modules``.

    Parameters
    ----------
    name:
        Dotted module path.
    stub:
        Module or object to return/register when the import fails.
    """
    module = _import_optional(name, fallback=stub)
    if module is not None:
        sys.modules.setdefault(name, module)
    return module


# Re-export for convenience
import_optional = _import_optional

__all__ = ["safe_import", "import_optional"]
