# Fix navbar by adding navigation links
with open('core/app_factory/__init__.py', 'r') as f:
    content = f.read()

# Replace the simple navbar with one that has navigation links
old_nav = '''        html.Nav([
            html.H3("🏯 Yōsai Dashboard", style={"color": "white", "padding": "15px", "margin": "0"}),
        ], style={"background": "#1f2937", "margin-bottom": "20px"}),'''

new_nav = '''        html.Nav([
            html.Div([
                html.H3("🏯 Yōsai Dashboard", style={"color": "white", "padding": "15px", "margin": "0", "display": "inline-block"}),
                html.Div([
                    html.A("Dashboard", href="/dashboard", style={"color": "white", "text-decoration": "none", "margin": "0 15px"}),
                    html.A("Analytics", href="/analytics", style={"color": "white", "text-decoration": "none", "margin": "0 15px"}),
                    html.A("Upload", href="/upload", style={"color": "white", "text-decoration": "none", "margin": "0 15px"}),
                    html.A("Graphs", href="/graphs", style={"color": "white", "text-decoration": "none", "margin": "0 15px"}),
                    html.A("Export", href="/export", style={"color": "white", "text-decoration": "none", "margin": "0 15px"}),
                    html.A("Settings", href="/settings", style={"color": "white", "text-decoration": "none", "margin": "0 15px"}),
                ], style={"display": "inline-block", "float": "right", "padding": "20px 15px"})
            ], style={"width": "100%"})
        ], style={"background": "#1f2937", "margin-bottom": "20px", "overflow": "hidden"}),'''

content = content.replace(old_nav, new_nav)

with open('core/app_factory/__init__.py', 'w') as f:
    f.write(content)

print("✅ Fixed navbar with navigation links")
