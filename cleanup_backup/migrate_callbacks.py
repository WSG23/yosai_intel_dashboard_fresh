#!/usr/bin/env python3
"""Fixed callback migration with safe file reading."""

import re
from pathlib import Path
from typing import Union

def safe_read_file(file_path):
    """Safely read a file with encoding detection."""
    path = Path(file_path)
    
    # Try multiple encodings
    for encoding in ['utf-8', 'latin-1', 'cp1252', 'iso-8859-1']:
        try:
            return path.read_text(encoding=encoding)
        except UnicodeDecodeError:
            continue
    
    # Final fallback
    return path.read_text(encoding='utf-8', errors='replace')

def migrate_file(path: Union[str, Path], backup: bool = True, show_diff: bool = False) -> bool:
    """Migrate callbacks in a single file."""
    path = Path(path)
    
    try:
        # FIXED: Use safe file reading
        text = safe_read_file(path)
    except Exception as e:
        print(f"Error reading {path}: {e}")
        return False
    
    original_text = text
    
    # Simple callback patterns
    patterns = [
        (re.compile(r'def\s+(\w+)_callback\s*\('), r'def handle_\1('),
        (re.compile(r'register_callback\s*\('), r'register_handler('),
        (re.compile(r'invoke_callback\s*\('), r'invoke_handler('),
    ]
    
    changes_made = False
    for pattern, replacement in patterns:
        new_text, count = pattern.subn(replacement, text)
        if count > 0:
            text = new_text
            changes_made = True
            if show_diff:
                print(f"Applied {count} replacements in {path}")
    
    if changes_made:
        if backup:
            backup_path = path.with_suffix(path.suffix + '.bak')
            backup_path.write_text(original_text, encoding='utf-8')
        
        try:
            path.write_text(text, encoding='utf-8')
            return True
        except Exception as e:
            print(f"Error writing {path}: {e}")
            return False
    
    return False

if __name__ == "__main__":
    print("Callback migration tool ready")
