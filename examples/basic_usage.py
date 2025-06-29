import os
import dash
from dash import html
from dash_csrf_plugin import DashCSRFPlugin
from core.secret_manager import SecretManager

app = dash.Dash(__name__)
manager = SecretManager()
app.server.config["SECRET_KEY"] = manager.get(
    "SECRET_KEY", os.getenv("SECRET_KEY", "change-me")
)

csrf = DashCSRFPlugin(app)

app.layout = html.Div([csrf.create_csrf_component(), html.H1("Basic CSRF Example")])

if __name__ == "__main__":
    app.run(debug=True)
