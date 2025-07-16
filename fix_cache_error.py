import re

print("Fixing cache error in core/__init__.py...")
with open("core/__init__.py", "r") as f:
    content = f.read()

content = re.sub(
    r"# from \.advanced_cache import AdvancedCacheManager, create_advanced_cache_manager, cache_with_lock  # Breaks circular import",
    "from .advanced_cache import AdvancedCacheManager, create_advanced_cache_manager, cache_with_lock",
    content,
)

with open("core/__init__.py", "w") as f:
    f.write(content)

print("✅ Re-enabled advanced_cache imports")
