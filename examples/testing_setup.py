"""Example testing configuration with CSRF disabled"""

import dash
from dash_csrf_plugin import DashCSRFPlugin, CSRFMode

app = dash.Dash(__name__)
app.server.config['SECRET_KEY'] = 'test-secret-key'

csrf = DashCSRFPlugin(app, mode=CSRFMode.TESTING)

app.layout = dash.html.Div([
    csrf.create_csrf_component(),
    dash.html.H1('Testing Setup')
])

if __name__ == '__main__':
    app.run_server(debug=True)
