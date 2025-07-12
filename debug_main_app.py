#!/usr/bin/env python3
"""Debug main app step by step to find circular import"""

print("🔍 Step 1: Testing basic imports...")

try:
    import dash
    print("✅ dash")
except Exception as e:
    print(f"❌ dash: {e}")

try:
    import dash_bootstrap_components as dbc
    print("✅ dash_bootstrap_components")
except Exception as e:
    print(f"❌ dash_bootstrap_components: {e}")

try:
    from core.app_factory import create_app
    print("✅ core.app_factory import")
except Exception as e:
    print(f"❌ core.app_factory import: {e}")
    exit(1)

print("\n🔍 Step 2: Testing simple app creation...")
try:
    app = create_app(mode="simple")
    print("✅ App created successfully")
    print(f"App type: {type(app)}")
    print(f"Layout type: {type(app.layout)}")
except Exception as e:
    print(f"❌ App creation failed: {e}")
    import traceback
    traceback.print_exc()
    exit(1)

print("\n🔍 Step 3: Testing callback access...")
try:
    # This is what fails in the real app
    dependencies = app._callback_list
    print(f"✅ Callback list accessible: {len(dependencies)} callbacks")
except Exception as e:
    print(f"❌ Callback list access failed: {e}")
    import traceback
    traceback.print_exc()

print("\n✅ Main app debugging complete!")
