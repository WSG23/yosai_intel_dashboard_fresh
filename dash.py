"""
Shim module to provide dash.no_update in environments
where dash.no_update is missing.
"""
try:
    # Try to import the real no_update if dash is installed
    from dash import no_update
except Exception:
    # Fallback stub
    no_update = None  # or use a sentinel object if preferred
__all__ = ["no_update"]
