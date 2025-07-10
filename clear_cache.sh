#!/bin/bash

echo "🧹 COMPREHENSIVE CACHE CLEARING"
echo "================================"

# 1. Force asset timestamps (cache busting)
echo "📁 Updating asset timestamps..."
find assets -name "*.css" -exec touch {} \;
find assets -name "*.js" -exec touch {} \;
find assets -name "*.png" -exec touch {} \;

# 2. Clear Python cache
echo "🐍 Clearing Python cache..."
find . -name "*.pyc" -delete
find . -name "__pycache__" -type d -exec rm -rf {} + 2>/dev/null || true

# 3. Clear any Flask/Dash cache
echo "🌶️ Clearing Flask cache..."
rm -rf flask_session/ 2>/dev/null || true
rm -rf .cache/ 2>/dev/null || true

# 4. Force main CSS update
echo "🎨 Force CSS reload..."
echo "/* Cache bust: $(date) */" >> assets/css/main.css

echo ""
echo "✅ Cache clearing complete!"
echo ""
echo "🔥 BROWSER STEPS:"
echo "   1. Hard Refresh: Cmd+Shift+R (Mac) or Ctrl+Shift+R (PC)"
echo "   2. Or Open DevTools > Right-click reload > Empty Cache and Hard Reload"
echo "   3. Or Browse Incognito/Private mode"
echo ""
echo "🚀 Restart your app: python3 app.py"

