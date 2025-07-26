from __future__ import annotations

from flask import Flask
from apispec import APISpec
from apispec.ext.marshmallow import MarshmallowPlugin
from flask_apispec import FlaskApiSpec



def create_flask_app() -> Flask:
    """Create a Flask app with all blueprints registered."""
    from upload_endpoint import upload_bp
    from device_endpoint import device_bp
    from mappings_endpoint import mappings_bp
    from yosai_intel_dashboard.src.adapters.api.settings_endpoint import settings_bp
    from yosai_intel_dashboard.src.adapters.api.analytics_endpoints import (
        analytics_bp,
        graphs_bp,
        export_bp,
    )
    from plugins.compliance_plugin.compliance_controller import compliance_bp
    import yosai_intel_dashboard.src.adapters.api.plugin_performance as plugin_perf
    import yosai_intel_dashboard.src.adapters.api.risk_scoring as risk

    app = Flask(__name__)
    app.register_blueprint(upload_bp)
    app.register_blueprint(device_bp)
    app.register_blueprint(mappings_bp)
    app.register_blueprint(settings_bp)
    app.register_blueprint(analytics_bp)
    app.register_blueprint(graphs_bp)
    app.register_blueprint(export_bp)
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
