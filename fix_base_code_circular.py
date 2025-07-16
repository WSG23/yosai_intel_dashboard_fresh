import re

# Fix core/advanced_cache.py - make config import lazy
print("Fixing core/advanced_cache.py...")
with open("core/advanced_cache.py", "r") as f:
    content = f.read()

# Remove the problematic top-level import
content = re.sub(
    r"from config\.config import get_cache_config",
    "# from config.config import get_cache_config  # Moved to lazy import",
    content,
)

# Find where get_cache_config is used and make it a lazy import
content = re.sub(
    r"(\s+)([^#\n]*get_cache_config\(\))",
    r"\1from config.config import get_cache_config  # Lazy import\n\1\2",
    content,
)

with open("core/advanced_cache.py", "w") as f:
    f.write(content)

print("✅ Fixed core/advanced_cache.py")

# Also check if there are other problematic imports in core/__init__.py
print("Checking core/__init__.py...")
with open("core/__init__.py", "r") as f:
    content = f.read()

# Comment out the advanced_cache import temporarily to break the cycle
content = re.sub(
    r"from \.advanced_cache import AdvancedCacheManager, create_advanced_cache_manager, cache_with_lock",
    "# from .advanced_cache import AdvancedCacheManager, create_advanced_cache_manager, cache_with_lock  # Breaks circular import",
    content,
)

with open("core/__init__.py", "w") as f:
    f.write(content)

print("✅ Fixed core/__init__.py")
print("🔧 Base code circular import should be resolved")
