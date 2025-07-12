#!/usr/bin/env python3
"""Fix the graphs page cache issue"""

# ISSUE: pages/graphs.py imports cache before app exists
# Line: from core.cache import cache  # ❌ Cache has no .app attribute

# SOLUTION: Initialize cache lazily in the layout function

print("EDIT pages/graphs.py:")
print("")
print("REPLACE this line:")
print("  from core.cache import cache")
print("")
print("WITH:")
print("  cache = None  # Initialize as None")
print("")
print("THEN in the layout() function, add at the top:")
print("  def layout():")
print("      global cache")
print("      if cache is None:")
print("          try:")
print("              from dash import current_app")
print("              if current_app:")
print("                  from flask_caching import Cache")
print("                  cache = Cache(current_app.server, config={'CACHE_TYPE': 'simple'})")
print("          except:")
print("              cache = None  # Fallback if no app context")
print("      # ... rest of layout function")
