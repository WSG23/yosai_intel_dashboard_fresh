#!/usr/bin/env python3
"""Quick fix script - run this to fix your Dash app issues"""

import os
import re
from pathlib import Path

def fix_file_imports(file_path):
    """Fix register_page imports in a file"""
    if not file_path.exists():
        print(f"⚠️  File not found: {file_path}")
        return
    
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Pattern to find the problematic import
    old_pattern = r'from dash import \((.*?)register_page,(.*?)\)'
    
    def replace_import(match):
        before = match.group(1)
        after = match.group(2)
        return f'from dash import ({before.rstrip()}{after.rstrip()}\n)\nfrom dash import register_page as dash_register_page'
    
    new_content = re.sub(old_pattern, replace_import, content, flags=re.DOTALL)
    
    if content != new_content:
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(new_content)
        print(f"✅ Fixed imports in {file_path.name}")
    else:
        print(f"ℹ️  No import issues in {file_path.name}")

def fix_aria_hidden(file_path):
    """Fix aria_hidden in navbar files"""
    if not file_path.exists():
        print(f"⚠️  File not found: {file_path}")
        return
    
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    new_content = content.replace('**{"aria-hidden": "true"}', '**{"aria-hidden": "true"}')
    
    if content != new_content:
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(new_content)
        print(f"✅ Fixed aria_hidden in {file_path.name}")
    else:
        print(f"ℹ️  No aria_hidden issues in {file_path.name}")

def create_env_file():
    """Create .env file if it doesn't exist"""
    env_path = Path('.env')
    if not env_path.exists():
        with open(env_path, 'w') as f:
            f.write("# Development environment\n")
            f.write("DB_PASSWORD=development_password\n")
        print("✅ Created .env file")
    else:
        print("ℹ️  .env file already exists")

# Run fixes
print("🔧 Running quick fixes for Dash app...\n")

# Fix page imports
page_files = [
    Path("pages/file_upload.py"),
    Path("pages/export.py"),
    Path("pages/settings.py"),
    Path("pages/deep_analytics.py"),
    Path("pages/graphs.py"),
]

for file_path in page_files:
    fix_file_imports(file_path)

# Fix navbar
navbar_files = [
    Path("components/ui/navbar.py"),
    Path("components/ui/navbar_enhanced.py"),
]

for file_path in navbar_files:
    fix_aria_hidden(file_path)

# Create environment file
create_env_file()

print("\n🎉 Quick fixes complete!")
print("\nNow run: python3 app.py")
