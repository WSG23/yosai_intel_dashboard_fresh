import sys
import types
import importlib

# Minimal stubs for optional dependencies
sys.modules.setdefault("redis", types.ModuleType("redis"))
sys.modules.setdefault("redis.asyncio", types.ModuleType("asyncio"))
flask_stub = types.ModuleType("flask")
flask_stub.request = object()
flask_stub.url_for = lambda *a, **k: ""
sys.modules.setdefault("flask", flask_stub)
sys.modules.setdefault("hvac", types.ModuleType("hvac"))

# Dash stubs
from tests.stubs import dash as dash_stub
sys.modules.setdefault("dash", dash_stub)
sys.modules.setdefault("dash.html", dash_stub.html)
sys.modules.setdefault("dash.dcc", dash_stub.dcc)
sys.modules.setdefault("dash.dependencies", dash_stub.dependencies)
sys.modules.setdefault("dash._callback", dash_stub._callback)
dash_stub.no_update = dash_stub._callback.NoUpdate()

from tests.stubs import dash_bootstrap_components as dbc_stub
sys.modules.setdefault("dash_bootstrap_components", dbc_stub)
if not hasattr(dbc_stub, "themes"):
    dbc_stub.themes = types.SimpleNamespace(BOOTSTRAP="bootstrap")
