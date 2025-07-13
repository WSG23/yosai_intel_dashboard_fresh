def _create_simple_app(assets_folder: str) -> "Dash":
    """Create simple Dash application for development"""
    try:
        from dash import dcc, html

        external_stylesheets = [dbc.themes.BOOTSTRAP]
        built_css = ASSETS_DIR / "dist" / "main.min.css"
        assets_ignore = r".*\.map|css/_.*"
        if built_css.exists():
            external_stylesheets.append("/assets/dist/main.min.css")
            assets_ignore += r"|css/main\.css"

        # ✅ FIXED: Create app FIRST
        app = dash.Dash(
            __name__,
            external_stylesheets=external_stylesheets,
            suppress_callback_exceptions=True,
            assets_folder=assets_folder,
            assets_ignore=assets_ignore,
            use_pages=True,
            pages_folder="",
        )
        
        # ✅ FIXED: THEN register pages (after app exists)
        try:
            from pages import register_pages
            register_pages()
            logger.info("✅ Pages registered successfully")
        except Exception as e:
            logger.warning(f"Page registration failed: {e}")

        fix_flask_mime_types(app)
        ensure_icon_cache_headers(app)

        cache = Cache(app.server, config={"CACHE_TYPE": "simple"})
        cast(Any, app).cache = cache

        app.index_string = f"""
<!DOCTYPE html>
<html>
  <head>
    {{%metas%}}
    <title>Yōsai Intel Dashboard</title>
    <link rel=\"stylesheet\" href=\"{BUNDLE}\" />
    {{%favicon%}}
    {{%css%}}
  </head>
  <body>
    {{%app_entry%}}
    <footer>{{%config%}}{{%scripts%}}{{%renderer%}}</footer>
  </body>
</html>
"""

        apply_theme_settings(app)

        # ✅ ENSURE page-content div exists in layout
        app.layout = html.Div([
            dcc.Location(id="url", refresh=False),
            html.H1("🏯 Yōsai Intel Dashboard", className="text-center"),
            html.Hr(),
            html.Div(id="page-content"),  # ✅ This is essential for routing!
            html.Div([
                dbc.Alert("✅ Application created successfully!", color="success"),
                dbc.Alert("⚠️ Running in simplified mode (no auth)", color="warning"),
                html.P("Environment configuration loaded and working."),
                html.P("Ready for development and testing."),
            ], className="container"),
        ])

        # Register callbacks after everything is set up
        config_manager = DummyConfigManager()
        _register_callbacks(app, config_manager, container=None)

        server = cast(Flask, app.server)
        _configure_swagger(server)
        register_health_endpoints(server)

        logger.info("Simple Dash application created successfully")
        return app

    except Exception as e:
        logger.error(f"Failed to create simple application: {e}")
        raise
