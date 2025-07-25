import dash

# Ensure dash.no_update exists for the import chain
if not hasattr(dash, "no_update"):
    dash.no_update = None

from yosai_intel_dashboard.src.core.callbacks import UnifiedCallbackManager
from yosai_intel_dashboard.src.core.truly_unified_callbacks import TrulyUnifiedCallbacks


def test_unified_callback_manager_alias():
    assert UnifiedCallbackManager is TrulyUnifiedCallbacks
