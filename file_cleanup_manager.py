#!/usr/bin/env python3
"""
Modular File Cleanup Manager for Python3 Projects
Handles Unicode surrogate characters and provides enterprise-grade cleanup.
"""

from __future__ import annotations

import json
import logging
import shutil
import sys
from pathlib import Path
from typing import Dict, List, Optional, Set, Tuple
import re
import subprocess

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class UnicodeHandler:
    """Handle Unicode surrogate characters that can't be encoded in UTF-8."""
    
    @staticmethod
    def safe_read_text(file_path: Path) -> str:
        """Safely read text file handling Unicode issues."""
        encodings = ['utf-8', 'utf-8-sig', 'latin-1', 'cp1252']
        
        for encoding in encodings:
            try:
                return file_path.read_text(encoding=encoding, errors='replace')
            except (UnicodeDecodeError, UnicodeError):
                continue
        
        # Final fallback with error replacement
        return file_path.read_text(encoding='utf-8', errors='replace')
    
    @staticmethod
    def clean_unicode_surrogates(text: str) -> str:
        """Remove Unicode surrogate characters that can't be encoded."""
        # Remove surrogate pairs (U+D800 to U+DFFF)
        return re.sub(r'[\uD800-\uDFFF]', '', text)


class LegacyDetector:
    """Detect legacy imports and references that need cleanup."""
    
    def __init__(self):
        self.unicode_patterns = {
            'unicode_processor_import': re.compile(r'from\s+core\.unicode_processor\s+import'),
            'unicode_processor_direct': re.compile(r'import\s+core\.unicode_processor'),
            'unicode_processor_usage': re.compile(r'core\.unicode_processor\.'),
        }
        
        self.callback_patterns = {
            'legacy_callback_import': re.compile(r'from\s+services\.data_processing\.callback_controller'),
            'legacy_callback_usage': re.compile(r'callback_controller\.'),
        }
    
    def scan_file(self, file_path: Path) -> Dict[str, List[int]]:
        """Scan file for legacy patterns and return line numbers."""
        if not file_path.exists() or file_path.suffix != '.py':
            return {}
        
        try:
            content = UnicodeHandler.safe_read_text(file_path)
            content = UnicodeHandler.clean_unicode_surrogates(content)
        except Exception as e:
            logger.warning(f"Could not read {file_path}: {e}")
            return {}
        
        findings = {}
        all_patterns = {**self.unicode_patterns, **self.callback_patterns}
        
        for pattern_name, pattern in all_patterns.items():
            matches = []
            for line_num, line in enumerate(content.splitlines(), 1):
                if pattern.search(line):
                    matches.append(line_num)
            
            if matches:
                findings[pattern_name] = matches
        
        return findings


class FileCleanupManager:
    """Main cleanup manager with modular approach."""
    
    def __init__(self, project_root: Path = None):
        self.project_root = project_root or Path.cwd()
        self.detector = LegacyDetector()
        self.backup_dir = self.project_root / "cleanup_backup"
        
        # Files to remove (organized by category)
        self.removable_files = {
            'legacy_unicode': [
                'core/unicode_processor.py',
                'tools/migration_validator.py',
                'tools/legacy_unicode_audit.py',
                'scripts/unicode_migration.py',
            ],
            'legacy_callbacks': [
                'services/data_processing/unified_callbacks.py',
            ],
            'cleanup_tools': [
                'tools/unicode_cleanup.py',
                'tools/unicode_cleanup_simple.py',
                'tools/complete_callback_cleanup.py',
                'tools/detect_legacy_callbacks.py',
                'tools/migrate_callbacks.py',
            ],
            'debug_examples': [
                'examples/debugcsv.py',
                'examples/legacy_lazystring_fix_plugin.py',
                'examples/debug_csv_test.py',
                'scripts/analyze_tests.py',
            ],
            'temp_directories': [
                'temp/uploaded_data/*.pkl',  # Legacy pickle files
                '__pycache__',
                '.pytest_cache',
                'htmlcov',
                '.cache',
            ]
        }
    
    def create_backup(self, files_to_remove: List[Path]) -> bool:
        """Create backup of files before removal."""
        try:
            self.backup_dir.mkdir(exist_ok=True)
            
            for file_path in files_to_remove:
                if file_path.exists():
                    backup_path = self.backup_dir / file_path.name
                    if file_path.is_file():
                        shutil.copy2(file_path, backup_path)
                        logger.info(f"Backed up: {file_path} -> {backup_path}")
            
            return True
        except Exception as e:
            logger.error(f"Backup failed: {e}")
            return False
    
    def scan_for_references(self) -> Dict[str, Dict[str, List[int]]]:
        """Scan all Python files for legacy references."""
        logger.info("Scanning for legacy references...")
        
        scan_results = {}
        python_files = list(self.project_root.rglob("*.py"))
        
        for py_file in python_files:
            # Skip test files and backup directory
            if any(part in py_file.parts for part in ['tests', 'test_', 'backup']):
                continue
            
            findings = self.detector.scan_file(py_file)
            if findings:
                scan_results[str(py_file.relative_to(self.project_root))] = findings
        
        return scan_results
    
    def validate_safe_removal(self) -> Tuple[bool, List[str]]:
        """Validate that files can be safely removed."""
        logger.info("Validating safe removal...")
        
        references = self.scan_for_references()
        issues = []
        
        if references:
            issues.append("Legacy references still exist:")
            for file_path, patterns in references.items():
                for pattern, lines in patterns.items():
                    issues.append(f"  {file_path}:{lines} - {pattern}")
        
        # Check if critical files would be removed
        critical_paths = [
            'app.py',
            'config/config.py',
            'core/__init__.py'
        ]
        
        for category, files in self.removable_files.items():
            for file_pattern in files:
                file_path = self.project_root / file_pattern
                if file_path.exists() and any(crit in str(file_path) for crit in critical_paths):
                    issues.append(f"Critical file marked for removal: {file_path}")
        
        return len(issues) == 0, issues
    
    def remove_files(self, category: str = None, dry_run: bool = True) -> Dict[str, List[str]]:
        """Remove files by category or all categories."""
        logger.info(f"{'DRY RUN: ' if dry_run else ''}Removing files...")
        
        results = {
            'removed': [],
            'not_found': [],
            'errors': []
        }
        
        categories = [category] if category else self.removable_files.keys()
        
        for cat in categories:
            if cat not in self.removable_files:
                logger.warning(f"Unknown category: {cat}")
                continue
            
            logger.info(f"Processing category: {cat}")
            
            for file_pattern in self.removable_files[cat]:
                file_path = self.project_root / file_pattern
                
                try:
                    if '*' in file_pattern:
                        # Handle glob patterns
                        pattern_path = Path(file_pattern)
                        parent = self.project_root / pattern_path.parent
                        if parent.exists():
                            for match in parent.glob(pattern_path.name):
                                self._remove_single_file(match, dry_run, results)
                    else:
                        self._remove_single_file(file_path, dry_run, results)
                
                except Exception as e:
                    error_msg = f"Error processing {file_pattern}: {e}"
                    results['errors'].append(error_msg)
                    logger.error(error_msg)
        
        return results
    
    def _remove_single_file(self, file_path: Path, dry_run: bool, results: Dict[str, List[str]]):
        """Remove a single file or directory."""
        if not file_path.exists():
            results['not_found'].append(str(file_path))
            return
        
        try:
            if dry_run:
                logger.info(f"Would remove: {file_path}")
                results['removed'].append(f"[DRY RUN] {file_path}")
            else:
                if file_path.is_dir():
                    shutil.rmtree(file_path)
                else:
                    file_path.unlink()
                
                logger.info(f"Removed: {file_path}")
                results['removed'].append(str(file_path))
        
        except Exception as e:
            error_msg = f"Failed to remove {file_path}: {e}"
            results['errors'].append(error_msg)
            logger.error(error_msg)
    
    def run_tests(self) -> bool:
        """Run tests to ensure cleanup didn't break anything."""
        logger.info("Running tests...")
        
        try:
            result = subprocess.run(
                [sys.executable, '-m', 'pytest', '--maxfail=5', '-q'],
                cwd=self.project_root,
                capture_output=True,
                text=True,
                timeout=300
            )
            
            if result.returncode == 0:
                logger.info("Tests passed!")
                return True
            else:
                logger.error(f"Tests failed:\n{result.stdout}\n{result.stderr}")
                return False
        
        except subprocess.TimeoutExpired:
            logger.error("Tests timed out")
            return False
        except Exception as e:
            logger.error(f"Error running tests: {e}")
            return False
    
    def cleanup_report(self) -> Dict:
        """Generate comprehensive cleanup report."""
        logger.info("Generating cleanup report...")
        
        references = self.scan_for_references()
        safe, issues = self.validate_safe_removal()
        
        # Count files by category
        file_counts = {}
        total_size = 0
        
        for category, files in self.removable_files.items():
            count = 0
            size = 0
            
            for file_pattern in files:
                file_path = self.project_root / file_pattern
                
                if '*' in file_pattern:
                    pattern_path = Path(file_pattern)
                    parent = self.project_root / pattern_path.parent
                    if parent.exists():
                        matches = list(parent.glob(pattern_path.name))
                        count += len(matches)
                        size += sum(f.stat().st_size for f in matches if f.exists())
                else:
                    if file_path.exists():
                        count += 1
                        size += file_path.stat().st_size
            
            file_counts[category] = {'count': count, 'size_bytes': size}
            total_size += size
        
        return {
            'project_root': str(self.project_root),
            'legacy_references_found': len(references),
            'safe_to_remove': safe,
            'validation_issues': issues,
            'file_counts_by_category': file_counts,
            'total_size_bytes': total_size,
            'references_detail': references
        }


def main():
    """Main execution function with consolidated callbacks."""
    import argparse
    
    parser = argparse.ArgumentParser(description='Modular file cleanup manager')
    parser.add_argument('--dry-run', action='store_true', help='Show what would be removed')
    parser.add_argument('--category', help='Specific category to clean up')
    parser.add_argument('--report-only', action='store_true', help='Generate report only')
    parser.add_argument('--backup', action='store_true', help='Create backup before removal')
    parser.add_argument('--run-tests', action='store_true', help='Run tests after cleanup')
    
    args = parser.parse_args()
    
    manager = FileCleanupManager()
    
    # Generate report
    report = manager.cleanup_report()
    print(json.dumps(report, indent=2))
    
    if args.report_only:
        return
    
    # Validate safety
    safe, issues = manager.validate_safe_removal()
    if not safe:
        logger.error("Cleanup validation failed:")
        for issue in issues:
            logger.error(f"  {issue}")
        sys.exit(1)
    
    # Create backup if requested
    if args.backup:
        files_to_backup = []
        for category, files in manager.removable_files.items():
            if not args.category or category == args.category:
                for file_pattern in files:
                    file_path = manager.project_root / file_pattern
                    if file_path.exists():
                        files_to_backup.append(file_path)
        
        if not manager.create_backup(files_to_backup):
            logger.error("Backup failed, aborting cleanup")
            sys.exit(1)
    
    # Perform cleanup
    results = manager.remove_files(args.category, args.dry_run)
    
    print("\nCleanup Results:")
    print(f"Removed: {len(results['removed'])} files")
    print(f"Not found: {len(results['not_found'])} files")
    print(f"Errors: {len(results['errors'])} files")
    
    if results['errors']:
        print("\nErrors:")
        for error in results['errors']:
            print(f"  {error}")
    
    # Run tests if requested and not dry run
    if args.run_tests and not args.dry_run:
        if not manager.run_tests():
            logger.error("Tests failed after cleanup!")
            sys.exit(1)


if __name__ == "__main__":
    main()