import asyncio
import logging
import os

from flask import Flask, Response, jsonify, request
from flask_cors import CORS
from flask_wtf.csrf import CSRFProtect, generate_csrf
from prometheus_client import CONTENT_TYPE_LATEST, Counter, generate_latest

from core.rbac import RBACService, create_rbac_service
from core.secrets_validator import validate_all_secrets
from services.security import require_token
from tracing import init_tracing

csrf = CSRFProtect()

logger = logging.getLogger("api")
handler = logging.StreamHandler()
handler.setFormatter(
    logging.Formatter(
        '{"time":"%(asctime)s","level":"%(levelname)s","msg":"%(message)s"}'
    )
)
logger.addHandler(handler)
logger.setLevel(logging.INFO)

from api.analytics_endpoints import register_analytics_blueprints
from settings_endpoint import settings_bp

from config.constants import API_PORT
from device_endpoint import device_bp
from mappings_endpoint import mappings_bp
from upload_endpoint import upload_bp


def create_api_app() -> Flask:
    """Create Flask API app with all blueprints registered."""
    validate_all_secrets()
    init_tracing("api")
    app = Flask(__name__)

    # Initialize RBAC service
    try:
        app.config["RBAC_SERVICE"] = asyncio.run(create_rbac_service())
    except Exception as exc:  # pragma: no cover - best effort
        logger.error("Failed to initialize RBAC service: %s", exc)
        app.config["RBAC_SERVICE"] = None

    app.config["SECRET_KEY"] = os.environ["SECRET_KEY"]

    csrf.init_app(app)

    @app.before_request
    def enforce_csrf() -> None:
        if request.method not in {"GET", "HEAD", "OPTIONS"}:
            csrf.protect()

    CORS(app)

    REQUEST_COUNT = Counter(
        "yosai_request_total", "Total HTTP requests", ["method", "endpoint", "status"]
    )

    @app.after_request
    def record_metrics(response):
        REQUEST_COUNT.labels(request.method, request.path, response.status_code).inc()
        return response

    @app.route("/metrics")
    def metrics():
        return Response(generate_latest(), mimetype=CONTENT_TYPE_LATEST)

    # Third-party analytics demo endpoints
    register_analytics_blueprints(app)

    # Core upload and mapping endpoints
    app.register_blueprint(upload_bp)
    app.register_blueprint(device_bp)
    app.register_blueprint(mappings_bp)
    app.register_blueprint(settings_bp)

    @app.route("/v1/csrf-token", methods=["GET"])
    def get_csrf_token():
        """Provide CSRF token for clients."""
        return jsonify({"csrf_token": generate_csrf()})

    return app


if __name__ == "__main__":
    app = create_api_app()
    print("\n🚀 Starting Yosai Intel Dashboard API...")
    print(f"   Available at: http://localhost:{API_PORT}")
    print(f"   Upload endpoint: http://localhost:{API_PORT}/v1/upload")

    app.run(host="0.0.0.0", port=API_PORT, debug=True)
