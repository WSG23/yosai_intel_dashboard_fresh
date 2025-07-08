#!/usr/bin/env python3
"""Simple Unicode cleanup that works."""

import json
import re
from pathlib import Path
from typing import Dict, List, Tuple

def safe_read_file(file_path):
    """Safely read a file with multiple encoding attempts."""
    path = Path(file_path)
    
    # Try common encodings
    for encoding in ['utf-8', 'latin-1', 'cp1252']:
        try:
            return path.read_text(encoding=encoding)
        except UnicodeDecodeError:
            continue
    
    # Final fallback
    return path.read_text(encoding='utf-8', errors='replace')

def scan_legacy_references(base_dir: str = ".") -> Dict[str, List[Tuple[str, int]]]:
    """Find references to the deprecated core.unicode_processor module."""
    patterns = {
        "from_import": re.compile(r"^\s*from\s+core\.unicode_processor\s+import", re.M),
        "import_module": re.compile(r"^\s*import\s+core\.unicode_processor(\s+as\s+\w+)?", re.M),
        "attribute_access": re.compile(r"\bcore\.unicode_processor\."),
    }

    found: Dict[str, List[Tuple[str, int]]] = {}
    count = 0
    
    for path in Path(base_dir).rglob("*.py"):
        count += 1
        if count % 10 == 0:
            print(f"Scanned {count} files...")
            
        try:
            text = safe_read_file(path)
        except Exception as e:
            print(f"Warning: Could not read {path}: {e}")
            continue
            
        matches: List[Tuple[str, int]] = []
        for key, pattern in patterns.items():
            for m in pattern.finditer(text):
                line = text.count("\n", 0, m.start()) + 1
                matches.append((key, line))
        
        if matches:
            found[str(path)] = matches
    
    return found

def update_imports(base_dir: str = ".") -> Dict[str, int]:
    """Update references to core.unicode_processor to core.unicode."""
    replacements = {
        re.compile(r"from\s+core\.unicode_processor\s+import"): "from core.unicode import",
        re.compile(r"import\s+core\.unicode_processor\b"): "import core.unicode",
        re.compile(r"\bcore\.unicode_processor\."): "core.unicode.",
    }

    modified: Dict[str, int] = {}
    count = 0
    
    for path in Path(base_dir).rglob("*.py"):
        count += 1
        if count % 10 == 0:
            print(f"Processed {count} files...")
            
        try:
            text = safe_read_file(path)
        except Exception as e:
            print(f"Warning: Could not read {path}: {e}")
            continue
            
        original = text
        change_count = 0
        
        for pattern, repl in replacements.items():
            text, n = pattern.subn(repl, text)
            change_count += n
        
        if text != original:
            try:
                path.write_text(text, encoding="utf-8")
                modified[str(path)] = change_count
            except Exception as e:
                print(f"Warning: Could not write {path}: {e}")
    
    return modified

def complete_unicode_cleanup(base_dir: str = ".") -> Dict[str, any]:
    """Complete Unicode cleanup with simple file handling."""
    
    print("🔍 Scanning for legacy Unicode references...")
    legacy_refs = scan_legacy_references(base_dir)
    
    print(f"📝 Found {len(legacy_refs)} files with legacy references")
    
    print("🔄 Updating imports...")
    updated_files = update_imports(base_dir)
    
    print(f"✅ Updated {len(updated_files)} files")
    
    return {
        "legacy_references_found": len(legacy_refs),
        "files_updated": len(updated_files),
        "legacy_references": legacy_refs,
        "updated_files": updated_files
    }

if __name__ == "__main__":
    try:
        result = complete_unicode_cleanup()
        print(json.dumps(result, indent=2))
    except KeyboardInterrupt:
        print("\n❌ Interrupted by user")
    except Exception as e:
        print(f"❌ Error during cleanup: {e}")
        import traceback
        traceback.print_exc()
