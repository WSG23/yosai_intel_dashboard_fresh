import asyncio
import os

from fastapi.middleware.wsgi import WSGIMiddleware
from flask import Flask, jsonify, request
from flask_cors import CORS
from flask_wtf.csrf import CSRFProtect, generate_csrf

from core.rbac import RBACService, create_rbac_service
from core.secrets_validator import validate_all_secrets
from services.security import require_token
from yosai_framework.service import BaseService

csrf = CSRFProtect()

from api.analytics_endpoints import init_cache_manager, register_analytics_blueprints
from settings_endpoint import settings_bp

from config.constants import API_PORT
from device_endpoint import device_bp
from mappings_endpoint import mappings_bp
from upload_endpoint import upload_bp


def create_api_app() -> "FastAPI":
    """Create API app registered on a BaseService."""
    validate_all_secrets()
    service = BaseService("api", "")
    service.start()
    app = Flask(__name__)

    # Initialize RBAC service
    try:
        app.config["RBAC_SERVICE"] = asyncio.run(create_rbac_service())
    except Exception as exc:  # pragma: no cover - best effort
        service.log.error("Failed to initialize RBAC service: %s", exc)
        app.config["RBAC_SERVICE"] = None

    app.config["SECRET_KEY"] = os.environ["SECRET_KEY"]

    csrf.init_app(app)

    @app.before_request
    def enforce_csrf() -> None:
        if request.method not in {"GET", "HEAD", "OPTIONS"}:
            csrf.protect()

    CORS(app)

    # Third-party analytics demo endpoints
    register_analytics_blueprints(app)
    service.app.add_event_handler("startup", init_cache_manager)

    # Core upload and mapping endpoints
    app.register_blueprint(upload_bp)
    app.register_blueprint(device_bp)
    app.register_blueprint(mappings_bp)
    app.register_blueprint(settings_bp)

    @app.route("/v1/csrf-token", methods=["GET"])
    def get_csrf_token():
        """Provide CSRF token for clients."""
        return jsonify({"csrf_token": generate_csrf()})

    service.app.mount("/", WSGIMiddleware(app))
    return service.app


if __name__ == "__main__":
    app = create_api_app()
    print("\n🚀 Starting Yosai Intel Dashboard API...")
    print(f"   Available at: http://localhost:{API_PORT}")
    print(f"   Upload endpoint: http://localhost:{API_PORT}/v1/upload")

    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=API_PORT)
