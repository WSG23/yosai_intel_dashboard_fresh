import dash

# Ensure dash.no_update exists for the import chain
if not hasattr(dash, "no_update"):
    dash.no_update = None

import importlib


def test_unified_callback_manager_removed():
    callbacks = importlib.import_module("core.callbacks")
    assert not hasattr(callbacks, "UnifiedCallbackManager")
