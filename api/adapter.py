from flask import Flask
from flask_cors import CORS

from api.analytics_endpoints import register_analytics_blueprints
from upload_endpoint import upload_bp
from device_endpoint import device_bp
from mappings_endpoint import mappings_bp
from config.constants import API_PORT


def create_api_app() -> Flask:
    """Create Flask API app with all blueprints registered."""
    app = Flask(__name__)
    CORS(app)

    # Third-party analytics demo endpoints
    register_analytics_blueprints(app)

    # Core upload and mapping endpoints
    app.register_blueprint(upload_bp)
    app.register_blueprint(device_bp)
    app.register_blueprint(mappings_bp)
    app.register_blueprint(settings_bp)

    return app


if __name__ == "__main__":
    app = create_api_app()
    print("\n🚀 Starting Yosai Intel Dashboard API...")
    print(f"   Available at: http://localhost:{API_PORT}")
    print(f"   Upload endpoint: http://localhost:{API_PORT}/api/v1/upload")
    app.run(host="0.0.0.0", port=API_PORT, debug=True)
