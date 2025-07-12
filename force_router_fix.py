#!/usr/bin/env python3
"""Force router registration fix"""

# Read the _register_callbacks function and find why _register_router_callbacks isn't called
with open('core/app_factory/__init__.py', 'r') as f:
    content = f.read()

# Find the _register_callbacks function
import re
pattern = r'def _register_callbacks\((.*?)\n\s*"""(.*?)"""(.*?)(?=\ndef |\nclass |\Z)'
match = re.search(pattern, content, re.DOTALL)

if match:
    func_content = match.group(3)
    print("🔍 Found _register_callbacks function")
    
    # Check if _register_router_callbacks is being called
    if '_register_router_callbacks(' in func_content:
        print("✅ _register_router_callbacks call found in function")
        
        # Look for conditions that might prevent it
        lines = func_content.split('\n')
        router_line_found = False
        for i, line in enumerate(lines):
            if '_register_router_callbacks(' in line:
                router_line_found = True
                print(f"📍 Router call at line: {line.strip()}")
                
                # Show context around the call
                start = max(0, i-5)
                end = min(len(lines), i+3)
                print("📍 Context:")
                for j in range(start, end):
                    marker = "👉 " if j == i else "   "
                    print(f"{marker}{lines[j]}")
                break
        
        if not router_line_found:
            print("❌ Router call not found despite being in content")
    else:
        print("❌ _register_router_callbacks call NOT found in function")
        print("This is the issue - the call is missing!")
        
        # Show the function structure to understand why
        lines = func_content.split('\n')[:30]  # First 30 lines
        print("📍 Function structure:")
        for line in lines:
            if line.strip():
                print(f"   {line}")
else:
    print("❌ Could not find _register_callbacks function")

print("\n💡 Next: We need to ensure _register_router_callbacks gets called")
