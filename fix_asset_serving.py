# Add proper asset serving to app factory
with open('core/app_factory/__init__.py', 'r') as f:
    content = f.read()

# Add Flask routes for serving assets after app creation
addition = '''
        # Add Flask routes for serving assets
        @app.server.route('/assets/<path:filename>')
        def serve_assets(filename):
            """Serve static assets."""
            import os
            from flask import send_from_directory
            assets_dir = os.path.join(os.path.dirname(__file__), '..', '..', 'assets')
            return send_from_directory(assets_dir, filename)
        
        @app.server.route('/assets/navbar_icons/<filename>')
        def serve_navbar_icons(filename):
            """Serve navbar icon assets."""
            import os
            from flask import send_from_directory
            icons_dir = os.path.join(os.path.dirname(__file__), '..', '..', 'assets', 'navbar_icons')
            return send_from_directory(icons_dir, filename)'''

# Insert after app creation but before layout setting
content = content.replace(
    'app = Dash(__name__, external_stylesheets=[dbc.themes.BOOTSTRAP])',
    'app = Dash(__name__, external_stylesheets=[dbc.themes.BOOTSTRAP])' + addition
)

with open('core/app_factory/__init__.py', 'w') as f:
    f.write(content)

print("✅ Added asset serving routes")
