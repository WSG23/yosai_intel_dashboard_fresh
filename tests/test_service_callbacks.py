from dash import Dash
from core.truly_unified_callbacks import TrulyUnifiedCallbacks
from services.upload.callbacks import UploadCallbacks
from services.analytics.callbacks import AnalyticsCallbacks


def test_coordinator_register_all_callbacks():
    app = Dash()
    coord = TrulyUnifiedCallbacks(app)

    coord.register_all_callbacks(UploadCallbacks, AnalyticsCallbacks)

    assert "handle_upload" in coord.registered_callbacks
    assert "analytics_operations" in coord.registered_callbacks
