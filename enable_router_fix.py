#!/usr/bin/env python3
"""Re-enable the disabled router callbacks"""

# Read the file
with open('core/app_factory/__init__.py', 'r') as f:
    content = f.read()

# Find and fix the commented out line
old_line = '            # # _register_router_callbacks(coordinator, unicode_proc)  # DISABLED  # DISABLED - conflicts with Dash Pages'
new_line = '            _register_router_callbacks(coordinator, unicode_proc)  # ✅ RE-ENABLED - custom routing needed'

if old_line in content:
    new_content = content.replace(old_line, new_line)
    
    # Write the fixed content
    with open('core/app_factory/__init__.py', 'w') as f:
        f.write(new_content)
    
    print("✅ Router callbacks RE-ENABLED successfully!")
    print("✅ Custom routing should now work")
    print("🎯 Test your app now!")
else:
    print("❌ Could not find the exact commented line to fix")
    print("Manual fix needed:")
    print("   Find this line in core/app_factory/__init__.py:")
    print("   # # _register_router_callbacks(coordinator, unicode_proc)")
    print("   Replace with:")
    print("   _register_router_callbacks(coordinator, unicode_proc)")
