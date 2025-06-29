import os
import dash
from dash import html
from dash_csrf_plugin import DashCSRFPlugin, CSRFConfig, CSRFMode
from core.secret_manager import SecretManager

manager = SecretManager()
secret_key = manager.get("SECRET_KEY", os.getenv("SECRET_KEY", "super-secret-key"))
config = CSRFConfig.for_production(secret_key, exempt_routes=["/health"])

app = dash.Dash(__name__)
app.server.config["SECRET_KEY"] = secret_key

csrf = DashCSRFPlugin(app, config=config, mode=CSRFMode.ENABLED)

app.layout = html.Div([csrf.create_csrf_component(), html.H1("Advanced CSRF Example")])

if __name__ == "__main__":
    app.run()
