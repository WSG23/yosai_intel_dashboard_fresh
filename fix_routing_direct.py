# Add direct Dash routing callback to app_factory
with open('core/app_factory/__init__.py', 'r') as f:
    content = f.read()

# Add direct callback registration
routing_code = '''
    # Direct Dash routing callback (bypass TrulyUnifiedCallbacks)
    @app.callback(Output("page-content", "children"), Input("url", "pathname"))
    def route_pages(pathname):
        if pathname == "/dashboard":
            return html.H1("🏠 Dashboard - Direct Callback Works!")
        elif pathname == "/analytics":
            return html.H1("📊 Analytics - Direct Callback Works!")
        elif pathname == "/upload":
            return html.H1("📤 Upload - Direct Callback Works!")
        else:
            return html.H1("🏯 Yōsai Dashboard - Direct Callback")
'''

# Insert before the return app statement
content = content.replace('    return app', routing_code + '\n    return app')

with open('core/app_factory/__init__.py', 'w') as f:
    f.write(content)

print("✅ Added direct Dash routing callback")
