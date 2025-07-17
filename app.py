from flask import Flask
from flask_cors import CORS
from config.service_registration import register_upload_services
from core.service_container import ServiceContainer

# Import blueprints
from upload_endpoint import upload_bp
from device_endpoint import device_bp
from mappings_endpoint import mappings_bp

app = Flask(__name__)
CORS(app)

# Initialize container and services
container = ServiceContainer()
register_upload_services(container)

# Register blueprints
app.register_blueprint(upload_bp)
app.register_blueprint(device_bp)
app.register_blueprint(mappings_bp)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5001, debug=True)
