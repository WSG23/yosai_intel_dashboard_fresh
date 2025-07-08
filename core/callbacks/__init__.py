"""Unified callback utilities.

``UnifiedCallbackManager`` is provided purely for backwards compatibility and
is simply an alias of :class:`TrulyUnifiedCallbacks`.
"""

from ..truly_unified_callbacks import Operation, TrulyUnifiedCallbacks

__all__ = ["Operation", "TrulyUnifiedCallbacks"]
