"""Example testing configuration with CSRF disabled"""

import os
import dash
from dash_csrf_plugin import DashCSRFPlugin, CSRFMode
from core.secret_manager import SecretManager

app = dash.Dash(__name__)
manager = SecretManager()
app.server.config["SECRET_KEY"] = manager.get(
    "SECRET_KEY", os.getenv("SECRET_KEY", "test-secret-key")
)

csrf = DashCSRFPlugin(app, mode=CSRFMode.TESTING)

app.layout = dash.html.Div(
    [csrf.create_csrf_component(), dash.html.H1("Testing Setup")]
)

if __name__ == "__main__":
    app.run(debug=True)
