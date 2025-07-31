import dash

# Ensure dash.no_update exists for the import chain
if not hasattr(dash, "no_update"):
    dash.no_update = None

from core.callbacks import TrulyUnifiedCallbacks


def test_unified_callback_manager_removed():
    import core.callbacks as cb

    assert not hasattr(cb, "UnifiedCallbackManager")
