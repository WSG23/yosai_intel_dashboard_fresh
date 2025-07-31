"""Unified callback utilities.

``UnifiedCallbackManager`` is provided purely for backwards compatibility and
is simply an alias of :class:`TrulyUnifiedCallbacks`.
"""

from core.truly_unified_callbacks import Operation, TrulyUnifiedCallbacks

# Alias kept for backwards compatibility
UnifiedCallbackManager = TrulyUnifiedCallbacks

__all__ = ["Operation", "TrulyUnifiedCallbacks", "UnifiedCallbackManager"]
