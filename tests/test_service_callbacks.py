import sys
import types

# Create minimal Dash stubs with Input/Output
stub_dash = types.ModuleType("dash")
class _Dash:
    def callback(self, *args, **kwargs):
        def decorator(func):
            return func
        return decorator
stub_dash.Dash = _Dash
stub_dash.no_update = None

class _IO:
    def __init__(self, component_id, component_property, **kwargs):
        self.component_id = component_id
        self.component_property = component_property
        for k, v in kwargs.items():
            setattr(self, k, v)

Input = Output = State = _IO
stub_dash.Input = Input
stub_dash.Output = Output
stub_dash.State = State
stub_dep = types.ModuleType("dash.dependencies")
stub_dep.Input = Input
stub_dep.Output = Output
stub_dep.State = State
stub_dash.html = types.SimpleNamespace(Div=lambda *a, **k: None)

sys.modules["dash"] = stub_dash
sys.modules["dash.dependencies"] = stub_dep

from core.truly_unified_callbacks import TrulyUnifiedCallbacks
from services.upload.callbacks import UploadCallbacks
from services.analytics.callbacks import AnalyticsCallbacks


def test_coordinator_register_all_callbacks():
    app = stub_dash.Dash()
    coord = TrulyUnifiedCallbacks(app)

    coord.register_all_callbacks(UploadCallbacks, AnalyticsCallbacks)

    assert "handle_upload" in coord.registered_callbacks
    assert "analytics_operations" in coord.registered_callbacks
