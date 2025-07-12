#!/usr/bin/env python3
"""Test app with full callback registration to find circular import"""

print("🔍 Testing full app with callback registration...")

try:
    from core.app_factory import create_app
    print("✅ App factory imported")
    
    # Create app (this worked in our debug)
    app = create_app(mode="simple")
    print("✅ App created")
    print(f"Callbacks before registration: {len(app._callback_list)}")
    
    # The real app.py probably calls something that registers more callbacks
    # Let's check what app.py actually does
    print("✅ Checking what app.py does...")
    
    with open('app.py', 'r') as f:
        content = f.read()
        print("app.py content:")
        print(content[:500] + "..." if len(content) > 500 else content)
        
except Exception as e:
    print(f"❌ Error: {e}")
    import traceback
    traceback.print_exc()
