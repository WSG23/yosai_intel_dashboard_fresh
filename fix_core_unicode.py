import re

# Fix config/unicode_sql_processor.py - remove core.unicode dependency
with open("config/unicode_sql_processor.py", "r") as f:
    content = f.read()

# Remove the core.unicode import
content = re.sub(
    r"from core\.unicode import contains_surrogates",
    "# from core.unicode import contains_surrogates  # Circular import - use local implementation",
    content,
)

# Add local implementation
local_impl = '''

def contains_surrogates(text):
    """Local implementation to break circular import"""
    if not isinstance(text, str):
        return False
    return any(0xD800 <= ord(char) <= 0xDFFF for char in text)

'''

# Add after the commented import
content = content.replace(
    "# from core.unicode import contains_surrogates  # Circular import - use local implementation",
    "# from core.unicode import contains_surrogates  # Circular import - use local implementation"
    + local_impl,
)

with open("config/unicode_sql_processor.py", "w") as f:
    f.write(content)

print("✅ Fixed core.unicode circular import")
