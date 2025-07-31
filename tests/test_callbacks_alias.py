import dash

# Ensure dash.no_update exists for the import chain
if not hasattr(dash, "no_update"):
    dash.no_update = None

import core.callbacks as callbacks


def test_unified_callback_manager_removed():
    assert not hasattr(callbacks, "UnifiedCallbackManager")
