import os

from flask import Flask, jsonify, request
from flask_cors import CORS
from flask_wtf.csrf import CSRFProtect, generate_csrf

from services.security import require_token

csrf = CSRFProtect()

from api.analytics_endpoints import register_analytics_blueprints
from settings_endpoint import settings_bp

from config.constants import API_PORT
from device_endpoint import device_bp
from mappings_endpoint import mappings_bp
from upload_endpoint import upload_bp


def create_api_app() -> Flask:
    """Create Flask API app with all blueprints registered."""
    app = Flask(__name__)

    try:
        app.config["SECRET_KEY"] = os.environ["SECRET_KEY"]
    except KeyError as exc:
        raise RuntimeError("SECRET_KEY environment variable is required") from exc

    csrf.init_app(app)
    CORS(app)

    @app.before_request
    def _check_token():
        if request.endpoint == "get_csrf_token":
            return None
        return require_token(lambda: None)()  # type: ignore

    # Third-party analytics demo endpoints
    register_analytics_blueprints(app)

    # Core upload and mapping endpoints
    app.register_blueprint(upload_bp)
    app.register_blueprint(device_bp)
    app.register_blueprint(mappings_bp)
    app.register_blueprint(settings_bp)

    @app.route("/api/v1/csrf-token", methods=["GET"])
    def get_csrf_token():
        """Provide CSRF token for clients."""
        return jsonify({"csrf_token": generate_csrf()})

    return app


if __name__ == "__main__":
    app = create_api_app()
    print("\n🚀 Starting Yosai Intel Dashboard API...")
    print(f"   Available at: http://localhost:{API_PORT}")
    print(f"   Upload endpoint: http://localhost:{API_PORT}/api/v1/upload")
    app.run(host="0.0.0.0", port=API_PORT, debug=True)
