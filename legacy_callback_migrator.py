#!/usr/bin/env python3
"""
Legacy Callback Migration Tool
Migrates callback_controller usage to unified callback system
"""

from __future__ import annotations

import logging
import re
import sys
from pathlib import Path
from typing import Dict, List, Tuple

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
logger = logging.getLogger(__name__)


class CallbackMigrator:
    """Migrate legacy callback patterns to unified system."""
    
    def __init__(self):
        self.migration_patterns = {
            # Legacy callback_controller patterns to new unified patterns
            r'callback_controller\.': 'unified_callbacks.',
            r'from\s+services\.data_processing\.callback_controller\s+import': 'from core.truly_unified_callbacks import',
            r'import\s+services\.data_processing\.callback_controller': 'from core.truly_unified_callbacks import TrulyUnifiedCallbacks',
            r'CallbackController\(': 'TrulyUnifiedCallbacks(',
            r'\.callback_controller': '.unified_callbacks',
        }
        
        # Import replacements needed at top of files
        self.import_replacements = {
            'services.data_processing.callback_controller': 'core.truly_unified_callbacks',
            'CallbackController': 'TrulyUnifiedCallbacks',
        }
    
    def safe_read_file(self, file_path: Path) -> str:
        """Safely read file with Unicode handling."""
        try:
            return file_path.read_text(encoding='utf-8')
        except UnicodeDecodeError:
            try:
                return file_path.read_text(encoding='latin-1')
            except Exception:
                return file_path.read_text(encoding='utf-8', errors='replace')
    
    def migrate_file(self, file_path: Path, dry_run: bool = True) -> Tuple[bool, List[str]]:
        """Migrate a single file's callback patterns."""
        if not file_path.exists() or file_path.suffix != '.py':
            return False, []
        
        try:
            original_content = self.safe_read_file(file_path)
            modified_content = original_content
            changes = []
            
            # Apply migration patterns
            for old_pattern, new_pattern in self.migration_patterns.items():
                old_content = modified_content
                modified_content = re.sub(old_pattern, new_pattern, modified_content)
                
                if modified_content != old_content:
                    matches = len(re.findall(old_pattern, old_content))
                    changes.append(f"Replaced {matches} instances of '{old_pattern}' with '{new_pattern}'")
            
            # Add necessary imports if callback patterns were changed
            if changes and 'TrulyUnifiedCallbacks' not in original_content:
                # Check if we need to add the import
                if 'unified_callbacks.' in modified_content or 'TrulyUnifiedCallbacks(' in modified_content:
                    # Add import at the top after existing imports
                    lines = modified_content.split('\n')
                    import_line = "from core.truly_unified_callbacks import TrulyUnifiedCallbacks"
                    
                    # Find where to insert the import
                    insert_index = 0
                    for i, line in enumerate(lines):
                        if line.startswith('import ') or line.startswith('from '):
                            insert_index = i + 1
                        elif line.strip() == '' and insert_index > 0:
                            break
                    
                    if import_line not in modified_content:
                        lines.insert(insert_index, import_line)
                        modified_content = '\n'.join(lines)
                        changes.append("Added TrulyUnifiedCallbacks import")
            
            # Write changes if not dry run and content changed
            if modified_content != original_content:
                if not dry_run:
                    file_path.write_text(modified_content, encoding='utf-8')
                    logger.info(f"Migrated: {file_path}")
                else:
                    logger.info(f"Would migrate: {file_path}")
                
                return True, changes
            
            return False, []
            
        except Exception as e:
            logger.error(f"Error migrating {file_path}: {e}")
            return False, [f"Error: {e}"]
    
    def migrate_specific_files(self, file_list: List[str], dry_run: bool = True) -> Dict[str, List[str]]:
        """Migrate specific files identified in the cleanup report."""
        results = {}
        
        for file_path_str in file_list:
            file_path = Path(file_path_str)
            
            if not file_path.exists():
                logger.warning(f"File not found: {file_path}")
                continue
            
            changed, changes = self.migrate_file(file_path, dry_run)
            
            if changed:
                results[str(file_path)] = changes
            else:
                logger.info(f"No changes needed for: {file_path}")
        
        return results
    
    def migrate_project(self, project_root: Path = None, dry_run: bool = True) -> Dict[str, List[str]]:
        """Migrate all Python files in the project."""
        if project_root is None:
            project_root = Path.cwd()
        
        results = {}
        python_files = list(project_root.rglob("*.py"))
        
        logger.info(f"Scanning {len(python_files)} Python files...")
        
        for py_file in python_files:
            # Skip test files and backup directories
            if any(part in py_file.parts for part in ['tests', 'test_', 'backup', '.git']):
                continue
            
            changed, changes = self.migrate_file(py_file, dry_run)
            
            if changed:
                results[str(py_file.relative_to(project_root))] = changes
        
        return results


def create_unified_callback_template(file_path: Path) -> str:
    """Create template code for files that need unified callbacks."""
    return '''
# Add this to your file if you need unified callbacks
from core.truly_unified_callbacks import TrulyUnifiedCallbacks

class YourClassName:
    def __init__(self, app=None):
        # Initialize unified callbacks
        self.unified_callbacks = TrulyUnifiedCallbacks(app) if app else None
    
    def setup_callbacks(self):
        """Setup callbacks using unified system."""
        if not self.unified_callbacks:
            return
        
        # Example callback registration
        @self.unified_callbacks.register_callback(
            Output("output-id", "children"),
            Input("input-id", "value"),
            callback_id="unique_callback_id",
            component_name="your_component"
        )
        def your_callback(value):
            return f"Processed: {value}"
    
    def trigger_event(self, event_type, data):
        """Trigger events using unified system."""
        if self.unified_callbacks:
            self.unified_callbacks.trigger_event(event_type, data)
'''


def main():
    """Main migration function."""
    import argparse
    
    parser = argparse.ArgumentParser(description='Migrate legacy callback patterns')
    parser.add_argument('--dry-run', action='store_true', help='Show what would be changed')
    parser.add_argument('--files', nargs='+', help='Specific files to migrate')
    parser.add_argument('--create-template', help='Create template file at specified path')
    
    args = parser.parse_args()
    
    migrator = CallbackMigrator()
    
    if args.create_template:
        template_path = Path(args.create_template)
        template_path.write_text(create_unified_callback_template(template_path))
        logger.info(f"Created template at: {template_path}")
        return
    
    # Files identified in the cleanup report that need migration
    problematic_files = [
        "security_unified_callbacks.py",
        "file_processing/data_processor.py", 
        "file_processing/format_detector.py",
        "file_processing/readers/fwf_reader.py",
        "file_processing/readers/excel_reader.py", 
        "file_processing/readers/csv_reader.py",
        "file_processing/readers/json_reader.py",
        "file_conversion/storage_manager.py",
        "analytics/security_patterns/analyzer.py"
    ]
    
    if args.files:
        # Migrate specific files provided by user
        results = migrator.migrate_specific_files(args.files, args.dry_run)
    else:
        # Migrate the known problematic files
        results = migrator.migrate_specific_files(problematic_files, args.dry_run)
    
    # Print results
    if results:
        print(f"\n{'DRY RUN: ' if args.dry_run else ''}Migration Results:")
        print("=" * 50)
        
        for file_path, changes in results.items():
            print(f"\n📁 {file_path}:")
            for change in changes:
                print(f"  ✓ {change}")
        
        print(f"\nTotal files {'would be ' if args.dry_run else ''}modified: {len(results)}")
        
        if args.dry_run:
            print("\nRun without --dry-run to apply changes")
    else:
        print("No files need migration or no changes required.")


if __name__ == "__main__":
    main()