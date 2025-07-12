#!/usr/bin/env python3
"""Fix app factory registration timing"""

# Read the current file
with open('core/app_factory/__init__.py', 'r') as f:
    content = f.read()

# Find and replace the problematic section
old_section = '''        _register_pages()

        app.title = "Yōsai Intel Dashboard"

        app.layout = html.Div(
            [
                dcc.Location(id="url", refresh=False),
                html.H1("🏯 Yōsai Intel Dashboard", className="text-center"),
                html.Hr(),
                html.Div(
                    [
                        dbc.Alert(
                            "✅ Application created successfully!", color="success"
                        ),
                        dbc.Alert(
                            "⚠️ Running in simplified mode (no auth)", color="warning"
                        ),
                        html.P("Environment configuration loaded and working."),
                        html.P("Ready for development and testing."),
                    ],
                    className="container",
                ),
            ]
        )'''

new_section = '''        app.title = "Yōsai Intel Dashboard"

        app.layout = html.Div(
            [
                dcc.Location(id="url", refresh=False),
                html.H1("🏯 Yōsai Intel Dashboard", className="text-center"),
                html.Hr(),
                html.Div(id="page-content"),
                html.Div(
                    [
                        dbc.Alert(
                            "✅ Application created successfully!", color="success"
                        ),
                        dbc.Alert(
                            "⚠️ Running in simplified mode (no auth)", color="warning"
                        ),
                        html.P("Environment configuration loaded and working."),
                        html.P("Ready for development and testing."),
                    ],
                    className="container",
                ),
            ]
        )

        try:
            from pages import register_pages
            register_pages()
            logger.info("✅ Pages registered successfully")
        except Exception as e:
            logger.warning(f"Page registration failed: {e}")'''

# Make the replacement
if old_section in content:
    new_content = content.replace(old_section, new_section)
    print("✅ Found and replaced the problematic section")
    
    # Write the fixed content
    with open('core/app_factory/__init__.py', 'w') as f:
        f.write(new_content)
    print("✅ File updated successfully")
else:
    print("❌ Could not find the exact section to replace")
    print("File may have been modified already")
