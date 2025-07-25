from yosai_intel_dashboard.src.adapters.api.adapter import create_api_app
from yosai_intel_dashboard.src.infrastructure.config.constants import API_PORT

app = create_api_app()

if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=API_PORT)
