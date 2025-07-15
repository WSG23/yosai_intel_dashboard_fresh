import re

# Fix config/base.py - remove the circular dependency
with open('config/base.py', 'r') as f:
    content = f.read()

# Remove the problematic import that causes the circle
content = re.sub(
    r'from \.dynamic_config import dynamic_config',
    '# Removed circular import - dynamic_config will be imported locally when needed',
    content
)

with open('config/base.py', 'w') as f:
    f.write(content)

print("✅ Fixed circular import in config/base.py")
