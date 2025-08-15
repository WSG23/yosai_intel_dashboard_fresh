# Troubleshooting

This guide covers solutions to common issues when setting up or running the dashboard.

## Flask CLI NameError

If running `python services/api/start_api.py` (the unified startup script) fails with a traceback ending in:

```
NameError: name '_env_file_callback' is not defined
```

Flask may have been installed incorrectly or corrupted. Reinstall Flask in your virtual environment:

```bash
pip install --force-reinstall "Flask>=2.2.5"
```

This restores the missing function in `flask/cli.py` and allows the dashboard to start normally.

## Blank Dash page / missing content

If the application starts without errors but the browser only shows a blank page,
verify that the Dash layout and callbacks are registered correctly and that
static assets are being served.

1. **Check the layout**: ensure `app.layout` is set to either a Dash component
   tree or a function returning one.

2. **Confirm callbacks**: page content often relies on callbacks. Register a
   simple routing callback to populate the page:

   ```python
   from dash import Input, Output, html, dcc

   app.layout = html.Div([
       dcc.Location(id="url"),
       html.Div(id="page-content")
   ])

   @app.callback(Output("page-content", "children"), Input("url", "pathname"))
   def display_page(pathname):
       if pathname == "/":
           return html.H1("Dashboard Home")
       return html.Div([html.H1("404"), html.P(f"No page '{pathname}'")])
   ```

3. **Validate assets**: check that the `assets/` directory exists and that the
   browser DevTools console does not show failed CSS or JavaScript requests.

Following these steps resolves most cases where the Dash server runs but no
content appears in the browser.
