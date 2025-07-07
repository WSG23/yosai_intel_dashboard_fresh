"""
Local shim to provide dash.no_update for tests.
"""
try:
    # If the real dash package exports no_update, use it
    from dash import no_update
except (ImportError, ModuleNotFoundError):
    # Fallback stub: a unique sentinel object
    class _NoUpdateSentinel:
        """Sentinel for no_update stub."""
        pass
    no_update = _NoUpdateSentinel()

__all__ = ["no_update"]
