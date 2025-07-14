# Fix pages/__init__.py to work with regular Dash callbacks
with open('pages/__init__.py', 'r') as f:
    content = f.read()

# Replace the TrulyUnifiedCallbacks routing with regular Dash callback
regular_routing = '''
def create_manual_router(app):
    """Create manual routing with regular Dash callbacks."""
    from dash import Input, Output, html
    
    @app.callback(
        Output("page-content", "children"),
        Input("url", "pathname"),
        prevent_initial_call=False
    )
    def route_pages(pathname):
        try:
            path_mapping = {
                "/": "deep_analytics",
                "/analytics": "deep_analytics", 
                "/dashboard": "deep_analytics",
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

# Remove the old functions and add the new one
import re
content = re.sub(r'def create_manual_router.*?(?=\n\ndef|\Z)', '', content, flags=re.DOTALL)
content = re.sub(r'def register_router_callback.*?(?=\n\ndef|\Z)', '', content, flags=re.DOTALL)
content += regular_routing

with open('pages/__init__.py', 'w') as f:
    f.write(content)

print("✅ Fixed routing for regular Dash callbacks")
