#!/usr/bin/env python3
"""Test full mode vs simple mode"""

print("🔍 Testing simple mode (working)...")
try:
    from core.app_factory import create_app
    app_simple = create_app(mode='simple')
    print("✅ Simple mode works")
    print(f"Simple mode callbacks: {len(app_simple._callback_list)}")
except Exception as e:
    print(f"❌ Simple mode failed: {e}")

print("\n🔍 Testing full mode (potentially broken)...")
try:
    from core.app_factory import create_app
    from pathlib import Path
    import os
    
    project_root = Path(__file__).resolve().parent
    assets_dir = os.path.normcase(os.path.abspath(project_root / "assets"))
    
    app_full = create_app(mode='full', assets_folder=assets_dir)
    print("✅ Full mode works")
    print(f"Full mode callbacks: {len(app_full._callback_list)}")
    
    # Test the exact thing that fails
    print("Testing callback list serialization...")
    dependencies = app_full._callback_list
    print(f"✅ Callback list access works: {len(dependencies)} callbacks")
    
except Exception as e:
    print(f"❌ Full mode failed: {e}")
    import traceback
    traceback.print_exc()
