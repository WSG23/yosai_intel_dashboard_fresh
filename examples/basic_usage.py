import dash
from dash import html
from dash_csrf_plugin import DashCSRFPlugin

app = dash.Dash(__name__)
app.server.config['SECRET_KEY'] = 'change-me'

csrf = DashCSRFPlugin(app)

app.layout = html.Div([
    csrf.create_csrf_component(),
    html.H1('Basic CSRF Example')
])

if __name__ == '__main__':
    app.run(debug=True)
