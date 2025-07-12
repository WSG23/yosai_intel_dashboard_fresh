#!/usr/bin/env python3
"""Fix app layout to include page-content div"""

print("EDIT core/app_factory/__init__.py in the create_app() function:")
print("")
print("FIND the app.layout section and ENSURE it includes:")
print("  app.layout = html.Div([")
print("      dcc.Location(id='url', refresh=False),")
print("      create_navbar_layout(),  # Your navbar")
print("      html.Div(id='page-content'),  # ✅ This is essential for routing")
print("  ])")
print("")
print("The page-content div is what your custom router populates!")
