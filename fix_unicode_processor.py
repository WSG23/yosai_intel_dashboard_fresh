import re

# Fix config/unicode_sql_processor.py - remove analytics_core dependency
with open("config/unicode_sql_processor.py", "r") as f:
    content = f.read()

# Remove the problematic import
content = re.sub(
    r"from analytics_core\.utils\.unicode_processor import UnicodeHelper",
    "# from analytics_core.utils.unicode_processor import UnicodeHelper  # Circular import - use local implementation",
    content,
)

# Add a simple fallback implementation
fallback_code = '''

class UnicodeHelper:
    """Fallback Unicode helper to break circular import"""
    
    @staticmethod
    def clean_text(text):
        """Simple Unicode cleaning"""
        if not isinstance(text, str):
            text = str(text)
        # Remove surrogate characters
        return ''.join(char for char in text if not (0xD800 <= ord(char) <= 0xDFFF))
    
    @staticmethod
    def safe_encode(text, encoding='utf-8'):
        """Safe encoding"""
        try:
            return text.encode(encoding)
        except UnicodeEncodeError:
            return text.encode(encoding, errors='replace')

'''

# Add the fallback after the commented import
content = content.replace(
    "# from analytics_core.utils.unicode_processor import UnicodeHelper  # Circular import - use local implementation",
    "# from analytics_core.utils.unicode_processor import UnicodeHelper  # Circular import - use local implementation"
    + fallback_code,
)

with open("config/unicode_sql_processor.py", "w") as f:
    f.write(content)

print("✅ Fixed unicode_sql_processor circular import")
