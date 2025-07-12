import dash
from dash import html, dcc, page_container

app = dash.Dash(__name__)

# Register test page
dash.register_page(__name__, path='/', name='Home')

def layout():
    return html.H1("MINIMAL TEST WORKS!")

# Simple layout
app.layout = html.Div([
    dcc.Location(id='url'),
    page_container
])

if __name__ == '__main__':
    app.run_server(debug=True, port=8051)
