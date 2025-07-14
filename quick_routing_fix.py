# Restore working routing for minimal app
with open('pages/__init__.py', 'w') as f:
    f.write('''#!/usr/bin/env python3
"""Pages routing system."""
import logging
logger = logging.getLogger(__name__)

def get_page_layout(page_name):
    """Get layout function for page."""
    try:
        if page_name == "deep_analytics":
            from pages.deep_analytics import layout
            return layout
        elif page_name == "file_upload":
            from pages.file_upload import layout  
            return layout
        elif page_name == "export":
            from pages.export import layout
            return layout
        elif page_name == "settings":
            from pages.settings import layout
            return layout
        elif page_name == "graphs":
            from pages.graphs import layout
            return layout
    except Exception as e:
        logger.error(f"Failed to load {page_name}: {e}")
    return None

def create_manual_router(app):
    """Create manual routing with regular Dash callbacks."""
    from dash import Input, Output, html
    
    @app.callback(
        Output("page-content", "children"),
        Input("url", "pathname")
    )
    def route_pages(pathname):
        try:
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
                ])
        except Exception as e:
            return html.Div([
                html.H1("Routing Error"), 
                html.P(f"Error: {str(e)}")
            ])
''')

print("✅ Restored working routing")
