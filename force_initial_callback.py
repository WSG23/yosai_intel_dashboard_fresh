# Fix the initial callback issue
with open('pages/__init__.py', 'r') as f:
    content = f.read()

# Replace prevent_initial_call=False with suppress_callback_exceptions=False and add clientside callback
new_routing = '''
def create_manual_router(app):
    """Create manual routing with regular Dash callbacks."""
    from dash import Input, Output, html, clientside_callback, ClientsideFunction
    
    # Force initial callback to fire
    app.clientside_callback(
        """
        function(pathname) {
            return pathname || window.location.pathname;
        }
        """,
        Output("url", "pathname"),
        Input("url", "pathname"),
    )
    
    @app.callback(
        Output("page-content", "children"),
        Input("url", "pathname")
    )
    def route_pages(pathname):
        try:
            # Default to dashboard if no pathname
            if not pathname or pathname == "/":
                pathname = "/dashboard"
                
            path_mapping = {
                "/dashboard": "deep_analytics",
                "/analytics": "deep_analytics", 
                "/upload": "file_upload",
                "/export": "export",
                "/settings": "settings",
                "/graphs": "graphs",
            }
            
            page_name = path_mapping.get(pathname, "deep_analytics")
            layout_func = get_page_layout(page_name)
            
            if layout_func:
                return layout_func()
            else:
                return html.Div([
                    html.H1("Page Not Found"),
                    html.P(f"Could not load page: {page_name}"),
                    html.P(f"Path: {pathname}")
                ])
        except Exception as e:
            return html.Div([
                html.H1("Routing Error"), 
                html.P(f"Error: {str(e)}")
            ])
'''

# Replace the routing function
import re
content = re.sub(r'def create_manual_router.*?(?=\Z)', new_routing, content, flags=re.DOTALL)

with open('pages/__init__.py', 'w') as f:
    f.write(content)

print("✅ Fixed initial callback firing")
