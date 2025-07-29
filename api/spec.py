from __future__ import annotations

from flask import Flask
from apispec import APISpec
from apispec.ext.marshmallow import MarshmallowPlugin
from flask_apispec import FlaskApiSpec
import os
import sys

# Ensure project root is on the path when executed directly
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

# Provide lightweight stubs for heavy dependencies when generating the spec
if os.environ.get("SPEC_STUBS"):
    import builtins
    import types
    import importlib

    real_import = builtins.__import__

    def stub_import(name, globals=None, locals=None, fromlist=(), level=0):
        try:
            return real_import(name, globals, locals, fromlist, level)
        except ModuleNotFoundError:
            if name.startswith(("services", "config", "core", "yosai_intel_dashboard", "mapping")):
                module = types.ModuleType(name)
                for attr in fromlist:
                    setattr(module, attr, object())
                sys.modules[name] = module
                return module
            raise
        except ImportError as exc:
            # Handle missing attribute imports
            if name.startswith(("services", "config", "core", "yosai_intel_dashboard", "mapping")):
                module = sys.modules.get(name)
                if module is None:
                    module = types.ModuleType(name)
                    sys.modules[name] = module
                for attr in fromlist:
                    setattr(module, attr, object())
                return module
            raise

    builtins.__import__ = stub_import

    container_stub = types.SimpleNamespace(has=lambda name: True, get=lambda name, *a, **k: None)
    service_registration_stub = types.ModuleType("config.service_registration")
    service_registration_stub.register_upload_services = lambda container: None
    sys.modules.setdefault("config.service_registration", service_registration_stub)

    core_container_stub = types.ModuleType("core.container")
    core_container_stub.container = container_stub
    sys.modules.setdefault("core.container", core_container_stub)

    # Map package namespace used in imports to local modules
    yd_mod = types.ModuleType("yosai_intel_dashboard")
    models_stub = types.ModuleType("yosai_intel_dashboard.models")
    models_stub.ModelRegistry = object
    yd_mod.models = models_stub
    sys.modules.setdefault("yosai_intel_dashboard.models", models_stub)
    sys.modules.setdefault("yosai_intel_dashboard", yd_mod)



def create_flask_app() -> Flask:
    """Create a Flask app with all blueprints registered."""
    from upload_endpoint import upload_bp
    from device_endpoint import device_bp
    from mappings_endpoint import mappings_bp
    from api.settings_endpoint import settings_bp
    from token_endpoint import token_bp
    from plugins.compliance_plugin.compliance_controller import compliance_bp
    import api.plugin_performance as plugin_perf
    import api.risk_scoring as risk

    app = Flask(__name__)
    app.register_blueprint(upload_bp)
    app.register_blueprint(device_bp)
    app.register_blueprint(mappings_bp)
    app.register_blueprint(settings_bp)
    app.register_blueprint(token_bp)
    app.register_blueprint(compliance_bp)

    # Attach additional routes that expect a global ``app`` variable.
    plugin_perf.app = app  # type: ignore[attr-defined]
    risk.app = app  # type: ignore[attr-defined]
    plugin_perf.PluginPerformanceAPI()  # registers routes on ``app``
    app.add_url_rule(
        "/api/v1/risk/score",
        view_func=risk.calculate_score_endpoint,
        methods=["POST"],
    )

    return app


def create_spec() -> APISpec:
    """Return an APISpec instance with all routes registered."""
    app = create_flask_app()
    endpoints = list(app.view_functions.items())

    app.config.update(
        {
            "APISPEC_SPEC": APISpec(
                title="Yosai Dashboard API",
                version="1.0.0",
                openapi_version="3.0.2",
                plugins=[MarshmallowPlugin()],
            )
        }
    )

    docs = FlaskApiSpec(app)
    for endpoint, view in endpoints:
        if endpoint == "static" or endpoint.startswith("flask-apispec"):
            continue
        blueprint = endpoint.split(".")[0] if "." in endpoint else None
        docs.register(view, blueprint=blueprint)

    return docs.spec


if __name__ == "__main__":  # pragma: no cover - manual spec generation
    import yaml

    spec = create_spec()
    print(yaml.safe_dump(spec.to_dict()))
