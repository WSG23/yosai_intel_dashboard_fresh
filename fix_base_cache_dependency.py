import re

print("Fixing utils/upload_store.py cache dependency...")
with open('utils/upload_store.py', 'r') as f:
    content = f.read()

content = re.sub(
    r'(\s+)(clear_cache\(\))',
    r'\1try:\n\1    clear_cache()\n\1except Exception as e:\n\1    # Cache not available in standalone mode\n\1    import logging\n\1    logging.getLogger(__name__).info(f"Cache clear skipped: {e}")',
    content
)

with open('utils/upload_store.py', 'w') as f:
    f.write(content)

print("✅ Fixed upload_store.py cache dependency")

print("Fixing advanced_cache.py for standalone usage...")
with open('advanced_cache.py', 'r') as f:
    content = f.read()

content = re.sub(
    r'def clear_cache\(\):.*?cache\.clear\(\)',
    '''def clear_cache():
    """Clear cache with fallback for standalone usage"""
    try:
        cache.clear()
    except (KeyError, RuntimeError, AttributeError) as e:
        # Cache not initialized in standalone mode - skip silently
        import logging
        logging.getLogger(__name__).debug(f"Cache clear skipped: {e}")''',
    content,
    flags=re.DOTALL
)

with open('advanced_cache.py', 'w') as f:
    f.write(content)

print("✅ Fixed advanced_cache.py for standalone usage")
