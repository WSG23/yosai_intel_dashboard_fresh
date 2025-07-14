# Add routing callback directly to app_factory
with open('core/app_factory/__init__.py', 'a') as f:
    f.write('''

def add_routing_callback(app, coordinator):
    """Add missing page routing callback."""
    from dash import Input, Output, html
    
    @coordinator.register_handler(
        Output("page-content", "children"),
        Input("url", "pathname"),
        callback_id="page_router", 
        component_name="router"
    )
    def display_page(pathname):
        if pathname == "/dashboard":
            return html.H1("🏠 Dashboard Works!")
        elif pathname == "/analytics":
            return html.H1("📊 Analytics Works!")  
        elif pathname == "/upload":
            return html.H1("📤 Upload Works!")
        else:
            return html.H1("🏯 Yōsai Dashboard")
    
    return app

# Find and modify _register_callbacks to call add_routing_callback
''')
print("✅ Added routing callback function")
