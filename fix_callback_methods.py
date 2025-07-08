#!/usr/bin/env python3
"""
Robust TrulyUnifiedCallbacks Method Fix Tool
============================================

This script intelligently fixes register_handler -> register_callback method name issues
in Python3 Dash applications using TrulyUnifiedCallbacks.

Features:
- Comprehensive codebase analysis
- Context-aware replacements
- Backup and rollback capability
- Unicode-safe handling
- Detailed reporting and validation
- Enterprise-grade error handling

Usage:
    python3 fix_callback_methods.py [--dry-run] [--backup] [--verbose]
"""

import argparse
import ast
import json
import logging
import os
import re
import shutil
import sys
import tempfile
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Tuple, Set, Optional, Any
import traceback


class CallbackMethodFixer:
    """Robust fixer for register_handler -> register_callback method calls."""
    
    def __init__(self, base_dir: str = ".", verbose: bool = False):
        self.base_dir = Path(base_dir).resolve()
        self.verbose = verbose
        self.backup_dir: Optional[Path] = None
        self.changes_made: Dict[str, Dict[str, Any]] = {}
        self.setup_logging()
        
    def setup_logging(self):
        """Setup comprehensive logging."""
        level = logging.DEBUG if self.verbose else logging.INFO
        logging.basicConfig(
            level=level,
            format='%(asctime)s - %(levelname)s - %(message)s',
            handlers=[
                logging.StreamHandler(sys.stdout),
                logging.FileHandler(f'callback_fix_{datetime.now().strftime("%Y%m%d_%H%M%S")}.log')
            ]
        )
        self.logger = logging.getLogger(__name__)
        
    def create_backup(self) -> Path:
        """Create a backup of all Python files."""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_dir = self.base_dir / f"backup_callback_fix_{timestamp}"
        backup_dir.mkdir(exist_ok=True)
        
        self.logger.info(f"Creating backup in {backup_dir}")
        
        python_files = list(self.base_dir.rglob("*.py"))
        for py_file in python_files:
            try:
                # Preserve directory structure
                rel_path = py_file.relative_to(self.base_dir)
                backup_file = backup_dir / rel_path
                backup_file.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(py_file, backup_file)
            except Exception as e:
                self.logger.warning(f"Failed to backup {py_file}: {e}")
                
        self.backup_dir = backup_dir
        self.logger.info(f"Backup created with {len(python_files)} files")
        return backup_dir
    
    def safe_read_file(self, file_path: Path) -> Optional[str]:
        """Safely read file content with Unicode handling."""
        try:
            # Try UTF-8 first
            with open(file_path, 'r', encoding='utf-8') as f:
                return f.read()
        except UnicodeDecodeError:
            try:
                # Fallback to UTF-8 with error handling
                with open(file_path, 'r', encoding='utf-8', errors='replace') as f:
                    content = f.read()
                    self.logger.warning(f"Unicode issues in {file_path}, using replacement chars")
                    return content
            except Exception as e:
                self.logger.error(f"Failed to read {file_path}: {e}")
                return None
    
    def safe_write_file(self, file_path: Path, content: str) -> bool:
        """Safely write file content with Unicode handling."""
        try:
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(content)
            return True
        except Exception as e:
            self.logger.error(f"Failed to write {file_path}: {e}")
            return False
    
    def analyze_python_file(self, file_path: Path) -> Dict[str, Any]:
        """Analyze a Python file for register_handler usage patterns."""
        analysis = {
            'file_path': str(file_path),
            'has_truly_unified_imports': False,
            'has_callback_controller_imports': False,
            'register_handler_calls': [],
            'register_callback_calls': [],
            'problematic_calls': [],
            'safe_calls': [],
            'syntax_valid': True,
            'import_analysis': {}
        }
        
        content = self.safe_read_file(file_path)
        if not content:
            return analysis
            
        try:
            # Parse the AST to understand the code structure
            tree = ast.parse(content)
            
            # Analyze imports
            for node in ast.walk(tree):
                if isinstance(node, ast.Import):
                    for alias in node.names:
                        if 'truly_unified_callbacks' in alias.name.lower():
                            analysis['has_truly_unified_imports'] = True
                        elif 'callback_controller' in alias.name.lower():
                            analysis['has_callback_controller_imports'] = True
                            
                elif isinstance(node, ast.ImportFrom):
                    if node.module and 'truly_unified_callbacks' in node.module.lower():
                        analysis['has_truly_unified_imports'] = True
                    elif node.module and 'callback_controller' in node.module.lower():
                        analysis['has_callback_controller_imports'] = True
                        
        except SyntaxError as e:
            analysis['syntax_valid'] = False
            self.logger.warning(f"Syntax error in {file_path}: {e}")
        except Exception as e:
            self.logger.warning(f"AST analysis failed for {file_path}: {e}")
        
        # Pattern matching for method calls
        register_handler_pattern = re.compile(
            r'(\w+)\.register_handler\s*\(',
            re.MULTILINE
        )
        
        register_callback_pattern = re.compile(
            r'(\w+)\.register_callback\s*\(',
            re.MULTILINE
        )
        
        # Find all register_handler calls
        for match in register_handler_pattern.finditer(content):
            line_num = content[:match.start()].count('\n') + 1
            object_name = match.group(1)
            
            call_info = {
                'line_number': line_num,
                'object_name': object_name,
                'full_match': match.group(0),
                'start_pos': match.start(),
                'end_pos': match.end()
            }
            
            analysis['register_handler_calls'].append(call_info)
            
            # Determine if this is problematic or safe
            if self.is_problematic_call(object_name, content, analysis):
                analysis['problematic_calls'].append(call_info)
            else:
                analysis['safe_calls'].append(call_info)
        
        # Find all register_callback calls for context
        for match in register_callback_pattern.finditer(content):
            line_num = content[:match.start()].count('\n') + 1
            object_name = match.group(1)
            
            analysis['register_callback_calls'].append({
                'line_number': line_num,
                'object_name': object_name,
                'full_match': match.group(0)
            })
            
        return analysis
    
    def is_problematic_call(self, object_name: str, content: str, analysis: Dict) -> bool:
        """Determine if a register_handler call is problematic (should be register_callback)."""
        
        # Known problematic patterns
        problematic_patterns = [
            'manager',      # Component callback managers
            'coord',        # TrulyUnifiedCallbacks coordinator
            'coordinator',  # TrulyUnifiedCallbacks coordinator
            'callbacks',    # TrulyUnifiedCallbacks instance
            'unified',      # UnifiedCallbackManager
        ]
        
        # Check if object name suggests TrulyUnifiedCallbacks
        if object_name.lower() in problematic_patterns:
            return True
            
        # Check for self._target pattern (CallbackUnifier)
        if 'self._target' in object_name:
            return True
            
        # Look for context clues in the surrounding code
        context_window = 200  # characters around the call
        
        # Find the line in content
        lines = content.split('\n')
        for i, line in enumerate(lines):
            if f'{object_name}.register_handler' in line:
                start_line = max(0, i - 5)
                end_line = min(len(lines), i + 5)
                context = '\n'.join(lines[start_line:end_line])
                
                # Look for TrulyUnifiedCallbacks indicators
                truly_unified_indicators = [
                    'TrulyUnifiedCallbacks',
                    'UnifiedCallbackManager', 
                    'callback_id=',
                    'component_name=',
                    'register_callback',
                    'unified_callback'
                ]
                
                if any(indicator in context for indicator in truly_unified_indicators):
                    return True
                    
                # Look for CallbackController indicators (safe)
                controller_indicators = [
                    'CallbackController',
                    'controller.register_handler',
                    'register_error_handler',
                    'fire_event',
                    'callback_handler'
                ]
                
                if any(indicator in context for indicator in controller_indicators):
                    return False
                    
        # Default to problematic if imports suggest TrulyUnifiedCallbacks usage
        if analysis.get('has_truly_unified_imports', False):
            return True
            
        return False
    
    def fix_file(self, file_path: Path, analysis: Dict, dry_run: bool = False) -> Dict[str, Any]:
        """Fix register_handler calls in a single file."""
        result = {
            'file_path': str(file_path),
            'replacements_made': 0,
            'lines_modified': [],
            'success': True,
            'error': None,
            'original_content': None,
            'new_content': None
        }
        
        if not analysis['problematic_calls']:
            return result
            
        content = self.safe_read_file(file_path)
        if not content:
            result['success'] = False
            result['error'] = "Could not read file"
            return result
            
        result['original_content'] = content
        new_content = content
        
        # Sort problematic calls by position (reverse order to preserve positions)
        problematic_calls = sorted(
            analysis['problematic_calls'], 
            key=lambda x: x['start_pos'], 
            reverse=True
        )
        
        # Replace each problematic call
        for call_info in problematic_calls:
            old_text = call_info['full_match']
            new_text = old_text.replace('register_handler', 'register_callback')
            
            # Replace in content
            start_pos = call_info['start_pos']
            end_pos = call_info['end_pos']
            
            new_content = (
                new_content[:start_pos] + 
                new_text + 
                new_content[end_pos:]
            )
            
            result['replacements_made'] += 1
            result['lines_modified'].append({
                'line_number': call_info['line_number'],
                'old_text': old_text,
                'new_text': new_text,
                'object_name': call_info['object_name']
            })
            
            self.logger.debug(
                f"Line {call_info['line_number']}: {old_text} -> {new_text}"
            )
        
        result['new_content'] = new_content
        
        # Write the file if not dry run
        if not dry_run and result['replacements_made'] > 0:
            if not self.safe_write_file(file_path, new_content):
                result['success'] = False
                result['error'] = "Failed to write file"
                
        return result
    
    def scan_codebase(self) -> Dict[str, Any]:
        """Scan the entire codebase for register_handler issues."""
        self.logger.info(f"Scanning codebase in {self.base_dir}")
        
        scan_results = {
            'total_files': 0,
            'files_with_issues': 0,
            'total_problematic_calls': 0,
            'total_safe_calls': 0,
            'file_analyses': {},
            'summary': {}
        }
        
        python_files = list(self.base_dir.rglob("*.py"))
        scan_results['total_files'] = len(python_files)
        
        for py_file in python_files:
            try:
                # Skip backup directories
                if 'backup_callback_fix_' in str(py_file):
                    continue
                    
                analysis = self.analyze_python_file(py_file)
                rel_path = str(py_file.relative_to(self.base_dir))
                scan_results['file_analyses'][rel_path] = analysis
                
                if analysis['problematic_calls']:
                    scan_results['files_with_issues'] += 1
                    scan_results['total_problematic_calls'] += len(analysis['problematic_calls'])
                    
                scan_results['total_safe_calls'] += len(analysis['safe_calls'])
                
            except Exception as e:
                self.logger.error(f"Error analyzing {py_file}: {e}")
                if self.verbose:
                    self.logger.debug(traceback.format_exc())
        
        # Generate summary
        scan_results['summary'] = {
            'files_needing_fixes': [
                path for path, analysis in scan_results['file_analyses'].items()
                if analysis['problematic_calls']
            ],
            'safe_files': [
                path for path, analysis in scan_results['file_analyses'].items()
                if analysis['safe_calls'] and not analysis['problematic_calls']
            ]
        }
        
        self.logger.info(f"Scan complete: {scan_results['files_with_issues']} files need fixes")
        return scan_results
    
    def fix_codebase(self, dry_run: bool = False) -> Dict[str, Any]:
        """Fix all register_handler issues in the codebase."""
        self.logger.info(f"Starting codebase fix (dry_run={dry_run})")
        
        # First scan to identify issues
        scan_results = self.scan_codebase()
        
        fix_results = {
            'scan_results': scan_results,
            'fixes_applied': {},
            'total_files_modified': 0,
            'total_replacements_made': 0,
            'errors': [],
            'success': True
        }
        
        if scan_results['total_problematic_calls'] == 0:
            self.logger.info("No problematic register_handler calls found!")
            return fix_results
        
        # Apply fixes to each problematic file
        for rel_path, analysis in scan_results['file_analyses'].items():
            if not analysis['problematic_calls']:
                continue
                
            file_path = self.base_dir / rel_path
            
            try:
                fix_result = self.fix_file(file_path, analysis, dry_run)
                fix_results['fixes_applied'][rel_path] = fix_result
                
                if fix_result['success'] and fix_result['replacements_made'] > 0:
                    fix_results['total_files_modified'] += 1
                    fix_results['total_replacements_made'] += fix_result['replacements_made']
                    
                    self.logger.info(
                        f"Fixed {rel_path}: {fix_result['replacements_made']} replacements"
                    )
                elif not fix_result['success']:
                    fix_results['errors'].append({
                        'file': rel_path,
                        'error': fix_result['error']
                    })
                    
            except Exception as e:
                error_msg = f"Failed to fix {rel_path}: {e}"
                self.logger.error(error_msg)
                fix_results['errors'].append({
                    'file': rel_path,
                    'error': str(e)
                })
                if self.verbose:
                    self.logger.debug(traceback.format_exc())
        
        if fix_results['errors']:
            fix_results['success'] = False
            
        return fix_results
    
    def validate_fixes(self) -> Dict[str, Any]:
        """Validate that fixes were applied correctly."""
        self.logger.info("Validating fixes...")
        
        validation_results = {
            'remaining_issues': [],
            'new_syntax_errors': [],
            'import_consistency': True,
            'success': True
        }
        
        # Re-scan for remaining issues
        scan_results = self.scan_codebase()
        
        if scan_results['total_problematic_calls'] > 0:
            validation_results['success'] = False
            validation_results['remaining_issues'] = [
                {
                    'file': path,
                    'calls': analysis['problematic_calls']
                }
                for path, analysis in scan_results['file_analyses'].items()
                if analysis['problematic_calls']
            ]
        
        # Check for new syntax errors
        for path, analysis in scan_results['file_analyses'].items():
            if not analysis['syntax_valid']:
                validation_results['new_syntax_errors'].append(path)
                validation_results['success'] = False
        
        if validation_results['success']:
            self.logger.info("✅ All fixes validated successfully!")
        else:
            self.logger.warning("⚠️ Validation found issues")
            
        return validation_results
    
    def generate_report(self, fix_results: Dict[str, Any], validation_results: Dict[str, Any]) -> str:
        """Generate a comprehensive fix report."""
        report = []
        report.append("=" * 80)
        report.append("TrulyUnifiedCallbacks Method Fix Report")
        report.append("=" * 80)
        report.append(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        report.append(f"Base Directory: {self.base_dir}")
        
        if self.backup_dir:
            report.append(f"Backup Directory: {self.backup_dir}")
        
        report.append("")
        
        # Summary
        scan = fix_results['scan_results']
        report.append("SUMMARY:")
        report.append(f"  Total Python files scanned: {scan['total_files']}")
        report.append(f"  Files with issues found: {scan['files_with_issues']}")
        report.append(f"  Total problematic calls: {scan['total_problematic_calls']}")
        report.append(f"  Total safe calls: {scan['total_safe_calls']}")
        report.append(f"  Files modified: {fix_results['total_files_modified']}")
        report.append(f"  Total replacements made: {fix_results['total_replacements_made']}")
        report.append("")
        
        # Files modified
        if fix_results['fixes_applied']:
            report.append("FILES MODIFIED:")
            for file_path, fix_result in fix_results['fixes_applied'].items():
                if fix_result['replacements_made'] > 0:
                    report.append(f"  {file_path}:")
                    report.append(f"    Replacements: {fix_result['replacements_made']}")
                    for mod in fix_result['lines_modified']:
                        report.append(f"    Line {mod['line_number']}: {mod['object_name']}.register_handler -> {mod['object_name']}.register_callback")
            report.append("")
        
        # Errors
        if fix_results['errors']:
            report.append("ERRORS:")
            for error in fix_results['errors']:
                report.append(f"  {error['file']}: {error['error']}")
            report.append("")
        
        # Validation
        report.append("VALIDATION:")
        if validation_results['success']:
            report.append("  ✅ All fixes validated successfully")
        else:
            if validation_results['remaining_issues']:
                report.append("  ❌ Remaining issues found:")
                for issue in validation_results['remaining_issues']:
                    report.append(f"    {issue['file']}: {len(issue['calls'])} problematic calls")
            
            if validation_results['new_syntax_errors']:
                report.append("  ❌ New syntax errors:")
                for file_path in validation_results['new_syntax_errors']:
                    report.append(f"    {file_path}")
        
        report.append("")
        report.append("NEXT STEPS:")
        if validation_results['success']:
            report.append("  1. Test your application: python3 app.py")
            report.append("  2. Run your test suite to ensure functionality")
            report.append("  3. If issues arise, restore from backup directory")
        else:
            report.append("  1. Review remaining issues listed above")
            report.append("  2. Manual intervention may be required")
            report.append("  3. Consider restoring from backup if needed")
        
        report.append("")
        report.append("=" * 80)
        
        return "\n".join(report)
    
    def rollback_from_backup(self, backup_dir: Path) -> bool:
        """Rollback changes using backup directory."""
        if not backup_dir.exists():
            self.logger.error(f"Backup directory not found: {backup_dir}")
            return False
            
        self.logger.info(f"Rolling back from backup: {backup_dir}")
        
        try:
            # Copy all files from backup back to original locations
            for backup_file in backup_dir.rglob("*.py"):
                rel_path = backup_file.relative_to(backup_dir)
                original_file = self.base_dir / rel_path
                
                # Ensure parent directory exists
                original_file.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(backup_file, original_file)
                
            self.logger.info("Rollback completed successfully")
            return True
            
        except Exception as e:
            self.logger.error(f"Rollback failed: {e}")
            return False


def main():
    """Main entry point for the callback method fixer."""
    parser = argparse.ArgumentParser(
        description="Fix register_handler -> register_callback method calls in TrulyUnifiedCallbacks"
    )
    parser.add_argument(
        '--dry-run', 
        action='store_true',
        help="Show what would be changed without making modifications"
    )
    parser.add_argument(
        '--backup', 
        action='store_true',
        help="Create backup before making changes"
    )
    parser.add_argument(
        '--verbose', '-v',
        action='store_true',
        help="Enable verbose logging"
    )
    parser.add_argument(
        '--base-dir',
        default=".",
        help="Base directory to scan (default: current directory)"
    )
    parser.add_argument(
        '--rollback',
        help="Rollback from specified backup directory"
    )
    
    args = parser.parse_args()
    
    # Handle rollback
    if args.rollback:
        fixer = CallbackMethodFixer(args.base_dir, args.verbose)
        backup_path = Path(args.rollback)
        success = fixer.rollback_from_backup(backup_path)
        sys.exit(0 if success else 1)
    
    # Normal operation
    fixer = CallbackMethodFixer(args.base_dir, args.verbose)
    
    try:
        # Create backup if requested
        backup_dir = None
        if args.backup and not args.dry_run:
            backup_dir = fixer.create_backup()
        
        # Fix the codebase
        fix_results = fixer.fix_codebase(args.dry_run)
        
        # Validate fixes (only if not dry run)
        validation_results = {'success': True}
        if not args.dry_run:
            validation_results = fixer.validate_fixes()
        
        # Generate and display report
        report = fixer.generate_report(fix_results, validation_results)
        print(report)
        
        # Save report to file
        report_file = f"callback_fix_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
        with open(report_file, 'w', encoding='utf-8') as f:
            f.write(report)
        print(f"\nDetailed report saved to: {report_file}")
        
        # Exit with appropriate code
        if args.dry_run:
            print(f"\n🔍 DRY RUN: Found {fix_results['scan_results']['total_problematic_calls']} issues to fix")
            print("Run without --dry-run to apply fixes")
        elif validation_results['success']:
            print("\n✅ All fixes completed successfully!")
        else:
            print("\n⚠️ Fixes completed with warnings - see report above")
            sys.exit(1)
            
    except KeyboardInterrupt:
        print("\n❌ Operation cancelled by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
        if args.verbose:
            traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()