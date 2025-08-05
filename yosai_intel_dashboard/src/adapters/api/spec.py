from __future__ import annotations

import os
import sys

from apispec import APISpec
from apispec.ext.marshmallow import MarshmallowPlugin
from flask import Blueprint, Flask
from flask_apispec import FlaskApiSpec

# Ensure project root is on the path when executed directly
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

# Provide lightweight stubs for heavy dependencies when generating the spec
if os.environ.get("SPEC_STUBS"):
    import builtins
    import types

    real_import = builtins.__import__

    def stub_import(name, globals=None, locals=None, fromlist=(), level=0):
        try:
            return real_import(name, globals, locals, fromlist, level)
        except ModuleNotFoundError:
            if name.startswith(
                ("services", "config", "core", "yosai_intel_dashboard", "mapping")
            ):
                module = types.ModuleType(name)
                for attr in fromlist:
                    setattr(module, attr, object())
                sys.modules[name] = module
                return module
            raise
        except ImportError:
            # Handle missing attribute imports
            if name.startswith(
                ("services", "config", "core", "yosai_intel_dashboard", "mapping")
            ):
                module = sys.modules.get(name)
                if module is None:
                    module = types.ModuleType(name)
                    sys.modules[name] = module
                for attr in fromlist:
                    setattr(module, attr, object())
                return module
            raise

    builtins.__import__ = stub_import

    # Provide lightweight stand-ins for utility decorators used by endpoints
    utils_stub = types.ModuleType("utils")

    decorators_stub = types.ModuleType("utils.pydantic_decorators")

    def _passthrough(_model=None):
        def decorator(func):
            return func

        return decorator

    decorators_stub.validate_input = _passthrough
    decorators_stub.validate_output = _passthrough
    utils_stub.pydantic_decorators = decorators_stub
    sys.modules.setdefault("utils", utils_stub)
    sys.modules.setdefault("utils.pydantic_decorators", decorators_stub)

    container_stub = types.SimpleNamespace(
        has=lambda name: True, get=lambda name, *a, **k: None
    )
    service_registration_stub = types.ModuleType("services.upload.service_registration")
    service_registration_stub.register_upload_services = lambda container: None
    sys.modules.setdefault(
        "services.upload.service_registration", service_registration_stub
    )

    core_container_stub = types.ModuleType("core.container")
    core_container_stub.container = container_stub
    core_container_stub.Container = object
    sys.modules.setdefault("core.container", core_container_stub)

    security_stub = types.ModuleType("services.security")
    security_stub.require_role = lambda role: (lambda func: func)
    security_stub.refresh_access_token = lambda token: "token"
    sys.modules.setdefault("services.security", security_stub)

    core_exceptions_stub = types.ModuleType("core.exceptions")

    class SecurityError(Exception):
        pass

    class ValidationError(Exception):
        pass

    core_exceptions_stub.SecurityError = SecurityError
    core_exceptions_stub.ValidationError = ValidationError
    sys.modules.setdefault("core.exceptions", core_exceptions_stub)

    config_stub = types.ModuleType("config")
    config_stub.get_security_config = lambda: {}
    sys.modules.setdefault("config", config_stub)

    # Map package namespace used in imports to local modules
    yd_mod = types.ModuleType("yosai_intel_dashboard")
    models_stub = types.ModuleType("yosai_intel_dashboard.models")
    models_stub.ModelRegistry = object
    yd_mod.models = models_stub
    sys.modules.setdefault("yosai_intel_dashboard.models", models_stub)
    sys.modules.setdefault("yosai_intel_dashboard", yd_mod)


def create_flask_app() -> Flask:
    """Create a Flask app with all blueprints registered."""
    from yosai_intel_dashboard.src.adapters.api.settings_endpoint import settings_bp
    from yosai_intel_dashboard.src.core.container import container
    from yosai_intel_dashboard.src.services.device_endpoint import (
        create_device_blueprint,
    )
    from yosai_intel_dashboard.src.services.feature_flags_endpoint import (
        create_feature_flags_blueprint,
    )
    from yosai_intel_dashboard.src.services.mappings_endpoint import (
        create_mappings_blueprint,
    )
    from yosai_intel_dashboard.src.services.token_endpoint import create_token_blueprint
    from yosai_intel_dashboard.src.services.upload_endpoint import (
        create_upload_blueprint,
    )

    if not os.environ.get("SPEC_STUBS"):
        from yosai_intel_dashboard.src.adapters.api import (
            plugin_performance as plugin_perf,
        )
        from yosai_intel_dashboard.src.adapters.api import risk_scoring as risk
        from yosai_intel_dashboard.src.adapters.api.plugins.compliance_plugin.compliance_controller import (
            compliance_bp,
        )
    else:
        compliance_bp = Blueprint(
            "compliance", __name__, url_prefix="/v1/complia" "nce"
        )
        plugin_perf = types.SimpleNamespace(app=None, PluginPerformanceAPI=lambda: None)
        risk = types.SimpleNamespace(calculate_score_endpoint=lambda: ("", 200))

    app = Flask(__name__)
    err_handler = (
        container.get("error_handler") if container.has("error_handler") else None
    )
    upload_bp = create_upload_blueprint(
        container.get("file_processor"),
        file_handler=(
            container.get("file_handler") if container.has("file_handler") else None
        ),
        handler=err_handler,
    )
    device_bp = create_device_blueprint(
        container.get("device_learning_service"),
        container.get("upload_processor"),
        handler=err_handler,
    )
    mappings_bp = create_mappings_blueprint(
        container.get("upload_processor"),
        container.get("device_learning_service"),
        container.get("consolidated_learning_service"),
        handler=err_handler,
    )
    token_bp = create_token_blueprint(handler=err_handler)
    flags_bp = create_feature_flags_blueprint(handler=err_handler)

    app.register_blueprint(upload_bp)
    app.register_blueprint(device_bp)
    app.register_blueprint(mappings_bp)
    app.register_blueprint(settings_bp)
    app.register_blueprint(flags_bp)
    app.register_blueprint(token_bp)
    app.register_blueprint(compliance_bp)

    # Attach additional routes that expect a global ``app`` variable.
    if not os.environ.get("SPEC_STUBS"):
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
