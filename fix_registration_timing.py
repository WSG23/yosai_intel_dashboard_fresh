#!/usr/bin/env python3
"""Fix page registration timing in app factory"""

# CURRENT ISSUE: In core/app_factory/__init__.py create_app():
# register_pages()  # ❌ Called BEFORE app creation
# app = dash.Dash(...)

# FIXED VERSION:
# 1. Create app first
# 2. Then register pages 
# 3. Keep your custom routing

print("EDIT core/app_factory/__init__.py create_app() function:")
print("MOVE the register_pages() call to AFTER app = dash.Dash(...)")
print("")
print("BEFORE:")
print("  register_pages()  # ❌ Too early")
print("  app = dash.Dash(...)")
print("")
print("AFTER:")
print("  app = dash.Dash(...)")
print("  register_pages()  # ✅ After app exists")
