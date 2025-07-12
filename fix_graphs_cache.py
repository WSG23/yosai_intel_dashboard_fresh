#!/usr/bin/env python3
"""Fix graphs page cache issue - pages/graphs.py needs app-aware cache initialization"""

# The error "Cache object has no attribute 'app'" means the graphs page
# is trying to access cache.app before the app exists.

# FIND THIS in pages/graphs.py:
# cache = Cache()  # ❌ This creates cache without app
# 
# REPLACE WITH:
# cache = None  # Initialize as None, set up during layout creation
# 
# def layout():
#     global cache
#     if cache is None:
#         from dash import current_app
#         if current_app:
#             cache = Cache(current_app.server)
#     return your_layout_content

print("Apply this fix to pages/graphs.py - initialize cache AFTER app creation")
