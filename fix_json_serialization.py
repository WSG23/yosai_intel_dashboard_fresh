#!/usr/bin/env python3
"""Fix JSON serialization issues with Unicode surrogate characters"""

import json
import re
import sys
from pathlib import Path

def remove_unicode_surrogates(text):
    """Remove Unicode surrogate characters that can't be encoded in UTF-8"""
    # Remove unpaired surrogates (U+D800 to U+DFFF)
    clean_text = re.sub(r'[\uD800-\uDFFF]', '', text)
    return clean_text

def fix_file_unicode_issues(filepath):
    """Fix Unicode issues in a Python file"""
    try:
        with open(filepath, 'r', encoding='utf-8', errors='replace') as f:
            content = f.read()
        
        # Remove Unicode surrogates
        cleaned_content = remove_unicode_surrogates(content)
        
        # Only write if changes were made
        if cleaned_content != content:
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(cleaned_content)
            print(f"✅ Fixed Unicode issues in {filepath}")
            return True
        else:
            print(f"✓ No Unicode issues found in {filepath}")
            return False
    except Exception as e:
        print(f"❌ Error processing {filepath}: {e}")
        return False

# Fix common files that might have Unicode issues
files_to_check = [
    "core/app_factory/__init__.py",
    "pages/deep_analytics.py", 
    "pages/graphs.py",
    "pages/export.py",
    "pages/settings.py",
    "pages/file_upload.py"
]

print("🔍 Checking for Unicode surrogate characters...")
fixed_count = 0

for filepath in files_to_check:
    if Path(filepath).exists():
        if fix_file_unicode_issues(filepath):
            fixed_count += 1

print(f"\n📊 Summary: Fixed {fixed_count} files")

# Also check for orjson installation issues
try:
    import orjson
    print("✅ orjson is installed")
    
    # Test basic serialization
    test_data = {"test": "value", "unicode": "hello 🎯"}
    orjson.dumps(test_data)
    print("✅ orjson basic serialization works")
    
except ImportError:
    print("❌ orjson not installed - installing...")
    import subprocess
    subprocess.run([sys.executable, "-m", "pip", "install", "orjson"])
    
except Exception as e:
    print(f"❌ orjson error: {e}")
    print("💡 May need to reinstall orjson")

print("\n🎯 Next: Test the app again")
