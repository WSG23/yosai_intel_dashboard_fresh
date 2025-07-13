#!/usr/bin/env python3
import os
import glob

def fix_aria_in_file(filepath):
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
        
        if 'aria_hidden="true"' in content:
            new_content = content.replace('aria_hidden="true"', '**{"aria-hidden": "true"}')
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(new_content)
            print(f"✅ Fixed {filepath}")
        else:
            print(f"ℹ️  No issues in {filepath}")
    except Exception as e:
        print(f"❌ Error with {filepath}: {e}")

# Fix all Python files
for pattern in ['pages/*.py', 'components/ui/*.py', 'components/*.py']:
    for filepath in glob.glob(pattern):
        fix_aria_in_file(filepath)

print("🎉 All aria_hidden issues fixed!")
