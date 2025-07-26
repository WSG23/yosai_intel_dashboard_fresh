from __future__ import annotations

"""Backwards compatible wrapper around :class:`TrulyUnifiedCallbacks`."""

"""Compatibility wrapper for :class:`TrulyUnifiedCallbacks`."""

from __future__ import annotations

from .truly_unified_callbacks import TrulyUnifiedCallbacks


class MasterCallbackSystem(TrulyUnifiedCallbacks):
    """Deprecated alias for :class:`TrulyUnifiedCallbacks`."""

    pass


__all__ = ["MasterCallbackSystem"]
