import dash
from dash import html
from dash_csrf_plugin import DashCSRFPlugin, CSRFConfig, CSRFMode

config = CSRFConfig.for_production('super-secret-key', exempt_routes=['/health'])

app = dash.Dash(__name__)
app.server.config['SECRET_KEY'] = config.secret_key

csrf = DashCSRFPlugin(app, config=config, mode=CSRFMode.ENABLED)

app.layout = html.Div([
    csrf.create_csrf_component(),
    html.H1('Advanced CSRF Example')
])

if __name__ == '__main__':
    app.run_server()
