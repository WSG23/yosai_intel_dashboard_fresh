#!/usr/bin/env python3
"""
Quick diagnosis script to understand why files aren't being detected
"""

import os
from pathlib import Path
from collections import Counter

def diagnose_project(project_path="."):
    """Diagnose why files might not be detected"""
    project_path = Path(project_path)
    
    print(f"\n🔍 DIAGNOSING PROJECT: {project_path.absolute()}")
    print("=" * 60)
    
    # Common exclude patterns
    exclude_dirs = {
        '.git', 'node_modules', '__pycache__', '.pytest_cache', 
        'venv', 'env', '.venv', 'dist', 'build', '.next',
        '.idea', '.vscode', 'coverage', 'htmlcov', 'vendor'
    }
    
    # File type counters
    all_files = Counter()
    excluded_files = Counter()
    included_files = Counter()
    
    # Directory analysis
    excluded_dirs_found = set()
    
    print("\n📁 Scanning directory structure...")
    
    for path in project_path.rglob('*'):
        if path.is_file():
            ext = path.suffix.lower()
            all_files[ext] += 1
            
            # Check if excluded
            path_parts = set(path.parts)
            excluded = False
            for exclude_dir in exclude_dirs:
                if exclude_dir in path_parts:
                    excluded = True
                    excluded_dirs_found.add(exclude_dir)
                    excluded_files[ext] += 1
                    break
            
            if not excluded:
                included_files[ext] += 1
    
    # Report findings
    print(f"\n📊 FILE STATISTICS:")
    print(f"   Total files found: {sum(all_files.values()):,}")
    print(f"   Files excluded: {sum(excluded_files.values()):,}")
    print(f"   Files to analyze: {sum(included_files.values()):,}")
    
    print(f"\n📂 EXCLUDED DIRECTORIES FOUND:")
    for dir_name in sorted(excluded_dirs_found):
        count = sum(1 for p in project_path.rglob('*') if dir_name in p.parts and p.is_file())
        print(f"   - {dir_name}: {count:,} files")
    
    print(f"\n📄 SOURCE FILES (Not Excluded):")
    source_extensions = ['.py', '.go', '.js', '.jsx', '.ts', '.tsx', '.java', '.cs']
    total_source = 0
    for ext in source_extensions:
        if included_files[ext] > 0:
            print(f"   {ext}: {included_files[ext]:,} files")
            total_source += included_files[ext]
    
    if total_source == 0:
        print("   ⚠️  NO SOURCE FILES FOUND!")
        
        # Check if files are in excluded dirs
        print(f"\n🚫 SOURCE FILES IN EXCLUDED DIRECTORIES:")
        for ext in source_extensions:
            if excluded_files[ext] > 0:
                print(f"   {ext}: {excluded_files[ext]:,} files (excluded)")
        
        # Show where Python files are
        print(f"\n🐍 PYTHON FILE LOCATIONS (first 10):")
        py_files = list(project_path.rglob('*.py'))[:10]
        for py_file in py_files:
            rel_path = py_file.relative_to(project_path)
            excluded = any(exc in py_file.parts for exc in exclude_dirs)
            status = "EXCLUDED" if excluded else "INCLUDED"
            print(f"   - {rel_path} [{status}]")
    
    print(f"\n💡 RECOMMENDATIONS:")
    if sum(excluded_files.values()) > sum(included_files.values()):
        print("   - Most files are in excluded directories")
        print("   - Consider if some directories shouldn't be excluded")
    
    if 'node_modules' in excluded_dirs_found and included_files['.js'] + included_files['.ts'] == 0:
        print("   - All JS/TS files appear to be in node_modules")
        print("   - Make sure your source code isn't being excluded")
    
    print("\n" + "=" * 60)
    
    return {
        'total_files': sum(all_files.values()),
        'excluded': sum(excluded_files.values()),
        'included': sum(included_files.values()),
        'source_files': total_source
    }

if __name__ == "__main__":
    import sys
    path = sys.argv[1] if len(sys.argv) > 1 else "."
    stats = diagnose_project(path)
    
    if stats['source_files'] == 0:
        print("\n❌ No source files will be analyzed!")
        print("   The multi_language_analyzer will fail with this project structure.")
        sys.exit(1)
    else:
        print(f"\n✅ Found {stats['source_files']} source files to analyze")
        print("   The multi_language_analyzer should work with this project.")
        