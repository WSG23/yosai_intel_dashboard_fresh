# Read the file and fix the broken layout assignments
with open('core/app_factory/__init__.py', 'r') as f:
    content = f.read()

# Fix the broken layout assignments by properly commenting out the entire blocks
import re

# Fix first broken layout (around line 585)
content = re.sub(
    r'        # app\.layout = html\.Div\(\s*\[\s*dcc\.Location\(id="url", refresh=False\),.*?\],?\s*\)',
    '        # Commented out competing layout assignment',
    content,
    flags=re.DOTALL
)

# Fix second broken layout (around line 696) 
content = re.sub(
    r'        # app\.layout = html\.Div\(\s*\[\s*html\.H1\("🏯 Yōsai Intel Dashboard".*?\],?\s*\)',
    '        # Commented out competing layout assignment',
    content,
    flags=re.DOTALL
)

# Write back
with open('core/app_factory/__init__.py', 'w') as f:
    f.write(content)
    
print("✅ Fixed syntax errors")
