import dash
import dash_bootstrap_components as dbc
from dash import html, dcc, Output, Input

from core.theme_manager import apply_theme_settings, sanitize_theme, DEFAULT_THEME


def create_theme_app():
    app = dash.Dash(__name__, external_stylesheets=[dbc.themes.BOOTSTRAP])
    apply_theme_settings(app)

    app.layout = html.Div(
        [
            dcc.Store(id="theme-store"),
            dcc.Dropdown(
                id="theme-dropdown",
                options=[
                    {"label": "Dark", "value": "dark"},
                    {"label": "Light", "value": "light"},
                    {"label": "High Contrast", "value": "high-contrast"},
                ],
                value=DEFAULT_THEME,
                clearable=False,
            ),
            html.Div(id="theme-dummy-output"),
        ]
    )

    @app.callback(Output("theme-store", "data"), Input("theme-dropdown", "value"))
    def update_theme_store(value):
        return sanitize_theme(value)

    app.clientside_callback(
        "function(data){if(window.setAppTheme&&data){window.setAppTheme(data);}return '';}",
        Output("theme-dummy-output", "children"),
        Input("theme-store", "data"),
    )

    return app


def test_theme_persistence_on_reload(dash_duo):
    app = create_theme_app()
    dash_duo.start_server(app)

    dropdown = dash_duo.find_element("#theme-dropdown")
    assert dropdown.get_attribute("value") == DEFAULT_THEME

    dash_duo.select_dcc_dropdown("#theme-dropdown", "light")
    dash_duo.wait_for(lambda: dash_duo.find_element("html").get_attribute("data-theme") == "light")

    dash_duo.driver.refresh()
    dash_duo.wait_for(lambda: dash_duo.find_element("html").get_attribute("data-theme") == "light")
    dropdown = dash_duo.find_element("#theme-dropdown")
    assert dropdown.get_attribute("value") == "light"
