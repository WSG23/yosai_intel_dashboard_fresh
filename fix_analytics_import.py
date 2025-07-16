import re

# Fix analytics_core/__init__.py - remove the problematic import
with open("analytics_core/__init__.py", "r") as f:
    content = f.read()

# Comment out the circular import
content = re.sub(
    r"from \.centralized_analytics_manager import CentralizedAnalyticsManager",
    "# from .centralized_analytics_manager import CentralizedAnalyticsManager  # Circular import - import locally when needed",
    content,
)

with open("analytics_core/__init__.py", "w") as f:
    f.write(content)

print("✅ Fixed analytics_core circular import")
