import dash

# Ensure dash.no_update exists for the import chain
if not hasattr(dash, "no_update"):
    dash.no_update = None

from core.callbacks import UnifiedCallbackManager
from core.truly_unified_callbacks import TrulyUnifiedCallbacks


def test_unified_callback_manager_alias():
    assert UnifiedCallbackManager is TrulyUnifiedCallbacks

