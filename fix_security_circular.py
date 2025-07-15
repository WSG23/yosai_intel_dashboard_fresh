import re

# Fix security/unicode_surrogate_validator.py - make import lazy
print("Fixing security/unicode_surrogate_validator.py...")
with open('security/unicode_surrogate_validator.py', 'r') as f:
    content = f.read()

# Remove the problematic top-level import
content = re.sub(
    r'from security_callback_controller import SecurityEvent, emit_security_event',
    '# from security_callback_controller import SecurityEvent, emit_security_event  # Lazy import to break circular',
    content
)

# Make the imports lazy where they're used
content = re.sub(
    r'(\s+)(emit_security_event\()',
    r'\1from security_callback_controller import emit_security_event  # Lazy import\n\1\2',
    content
)

content = re.sub(
    r'(\s+)(SecurityEvent\()',
    r'\1from security_callback_controller import SecurityEvent  # Lazy import\n\1\2',
    content
)

with open('security/unicode_surrogate_validator.py', 'w') as f:
    f.write(content)

print("✅ Fixed security/unicode_surrogate_validator.py")
