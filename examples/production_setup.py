"""Example production configuration using the CSRF plugin"""

import dash
from dash_csrf_plugin import DashCSRFPlugin, CSRFConfig, CSRFMode

app = dash.Dash(__name__)
app.server.config['SECRET_KEY'] = 'prod-secret-key'

config = CSRFConfig.for_production('prod-secret-key')
csrf = DashCSRFPlugin(app, config=config, mode=CSRFMode.PRODUCTION)

app.layout = dash.html.Div([
    csrf.create_csrf_component(),
    dash.html.H1('Production Setup')
])

if __name__ == '__main__':
    app.run(debug=False)
