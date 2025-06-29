"""Example production configuration using the CSRF plugin"""

import os
import dash
from dash_csrf_plugin import DashCSRFPlugin, CSRFConfig, CSRFMode
from core.secret_manager import SecretManager

app = dash.Dash(__name__)
manager = SecretManager()
secret_key = manager.get("SECRET_KEY", os.getenv("SECRET_KEY", "prod-secret-key"))
app.server.config["SECRET_KEY"] = secret_key

config = CSRFConfig.for_production(secret_key)
csrf = DashCSRFPlugin(app, config=config, mode=CSRFMode.PRODUCTION)

app.layout = dash.html.Div(
    [csrf.create_csrf_component(), dash.html.H1("Production Setup")]
)

if __name__ == "__main__":
    app.run(debug=False)
