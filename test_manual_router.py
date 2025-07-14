import os
os.environ["DB_PASSWORD"] = "test_password"
os.environ["SECRET_KEY"] = "test_key"

from core.app_factory import create_app
app = create_app()

# Try to register router callback manually
try:
    from pages import register_router_callback
    if hasattr(app, "_unified_wrapper"):
        register_router_callback(app._unified_wrapper)
        print("✅ Router callback registered manually")
    else:
        print("❌ No unified wrapper found")
except Exception as e:
    print(f"❌ Failed to register router: {e}")

if __name__ == "__main__":
    app.run_server(host="127.0.0.1", port=8052, debug=True)
