#!/usr/bin/env python3
"""
Automated Code Review Analyzer for Yosai Intel Dashboard
Performs static analysis to support manual code review
"""

import ast
import os
import re
from pathlib import Path
from typing import Dict, List, Set, Tuple
from collections import defaultdict, Counter
import json


class CodeAnalyzer:
    """Analyzes Python code for quality, redundancy, and best practices"""
    
    def __init__(self, project_path: str):
        self.project_path = Path(project_path)
        self.issues = defaultdict(list)
        self.metrics = {}
        # Directories to exclude from analysis
        self.exclude_dirs = {'.git', 'node_modules', '__pycache__', '.pytest_cache', 
                           'venv', 'env', '.venv', 'dist', 'build', '.next'}
        
    def analyze_project(self) -> Dict:
        """Run complete analysis on the project"""
        results = {
            'redundancy': self.find_redundant_code(),
            'callbacks': self.analyze_callbacks(),
            'unicode_issues': self.check_unicode_handling(),
            'python3_compliance': self.check_python3_compliance(),
            'modularity': self.assess_modularity(),
            'api_analysis': self.analyze_apis(),
            'security_issues': self.security_scan(),
            'performance_issues': self.performance_analysis()
        }
        return results
    
    def _get_python_files(self) -> List[Path]:
        """Get all Python files, excluding certain directories"""
        python_files = []
        for py_file in self.project_path.rglob('*.py'):
            # Skip files in excluded directories
            if any(excluded in py_file.parts for excluded in self.exclude_dirs):
                continue
            python_files.append(py_file)
        return python_files
    
    def find_redundant_code(self) -> Dict:
        """Identify duplicate and redundant code blocks"""
        duplicates = defaultdict(list)
        function_signatures = defaultdict(list)
        
        python_files = self._get_python_files()
        
        for py_file in python_files:
            try:
                with open(py_file, 'r', encoding='utf-8') as f:
                    tree = ast.parse(f.read())
                    
                for node in ast.walk(tree):
                    if isinstance(node, ast.FunctionDef):
                        # Create function signature
                        sig = self._get_function_signature(node)
                        function_signatures[sig].append({
                            'file': str(py_file.relative_to(self.project_path)),
                            'line': node.lineno,
                            'name': node.name
                        })
            except Exception as e:
                self.issues['parse_errors'].append(f"{py_file}: {e}")
        
        # Find duplicates
        for sig, locations in function_signatures.items():
            if len(locations) > 1:
                duplicates[sig] = locations
                
        return {'duplicates': dict(duplicates), 'total_functions': sum(len(v) for v in function_signatures.values())}
    
    def analyze_callbacks(self) -> Dict:
        """Find and analyze callback patterns"""
        callbacks = defaultdict(list)
        callback_patterns = [
            r'callback\s*=',
            r'on[A-Z]\w+\s*=',
            r'\.subscribe\(',
            r'\.then\(',
            r'addEventListener\('
        ]
        
        for py_file in self.project_path.rglob('*.py'):
            try:
                with open(py_file, 'r', encoding='utf-8') as f:
                    content = f.read()
                    
                for pattern in callback_patterns:
                    matches = re.finditer(pattern, content)
                    for match in matches:
                        line_no = content[:match.start()].count('\n') + 1
                        callbacks[str(py_file)].append({
                            'pattern': pattern,
                            'line': line_no,
                            'context': content[max(0, match.start()-50):match.end()+50]
                        })
            except Exception as e:
                self.issues['callback_errors'].append(f"{py_file}: {e}")
                
        return {
            'callbacks_found': dict(callbacks),
            'total_callbacks': sum(len(v) for v in callbacks.values()),
            'consolidation_opportunities': self._find_callback_consolidation(callbacks)
        }
    
    def check_unicode_handling(self) -> Dict:
        """Check for proper Unicode and UTF-8 handling"""
        unicode_issues = []
        proper_handling = []
        
        patterns = {
            'good': [
                r'encoding\s*=\s*[\'"]utf-8[\'"]',
                r'\.encode\([\'"]utf-8[\'"]',
                r'\.decode\([\'"]utf-8[\'"]'
            ],
            'bad': [
                r'\.encode\(\)',  # No encoding specified
                r'\.decode\(\)',  # No encoding specified
                r'str\(.+\)',     # Potential encoding issues
            ]
        }
        
        for py_file in self.project_path.rglob('*.py'):
            try:
                with open(py_file, 'r', encoding='utf-8') as f:
                    content = f.read()
                    
                for pattern in patterns['bad']:
                    matches = re.finditer(pattern, content)
                    for match in matches:
                        line_no = content[:match.start()].count('\n') + 1
                        unicode_issues.append({
                            'file': str(py_file),
                            'line': line_no,
                            'issue': f"Potential encoding issue: {match.group()}"
                        })
                        
                for pattern in patterns['good']:
                    if re.search(pattern, content):
                        proper_handling.append(str(py_file))
                        
            except Exception as e:
                self.issues['unicode_errors'].append(f"{py_file}: {e}")
                
        return {
            'issues': unicode_issues,
            'files_with_proper_handling': list(set(proper_handling)),
            'recommendation': "Ensure all string encoding/decoding uses explicit UTF-8"
        }
    
    def check_python3_compliance(self) -> Dict:
        """Verify Python 3 compliance"""
        py2_patterns = {
            'print_statement': r'print\s+[^(]',
            'xrange': r'\bxrange\s*\(',
            'unicode_literal': r'\bunicode\s*\(',
            'iteritems': r'\.iteritems\s*\(',
            'iterkeys': r'\.iterkeys\s*\(',
            'itervalues': r'\.itervalues\s*\(',
            'raw_input': r'\braw_input\s*\(',
            'execfile': r'\bexecfile\s*\('
        }
        
        compliance_issues = defaultdict(list)
        
        for py_file in self.project_path.rglob('*.py'):
            try:
                with open(py_file, 'r', encoding='utf-8') as f:
                    content = f.read()
                    
                for name, pattern in py2_patterns.items():
                    matches = re.finditer(pattern, content)
                    for match in matches:
                        line_no = content[:match.start()].count('\n') + 1
                        compliance_issues[str(py_file)].append({
                            'type': name,
                            'line': line_no,
                            'code': match.group()
                        })
                        
            except Exception as e:
                self.issues['py3_errors'].append(f"{py_file}: {e}")
                
        return {
            'python2_code_found': dict(compliance_issues),
            'is_compliant': len(compliance_issues) == 0
        }
    
    def assess_modularity(self) -> Dict:
        """Assess code modularity"""
        module_metrics = {}
        
        for py_file in self.project_path.rglob('*.py'):
            try:
                with open(py_file, 'r', encoding='utf-8') as f:
                    tree = ast.parse(f.read())
                    
                functions = [n for n in ast.walk(tree) if isinstance(n, ast.FunctionDef)]
                classes = [n for n in ast.walk(tree) if isinstance(n, ast.ClassDef)]
                
                # Calculate metrics
                avg_function_length = 0
                if functions:
                    lengths = [n.end_lineno - n.lineno for n in functions if n.end_lineno]
                    avg_function_length = sum(lengths) / len(lengths) if lengths else 0
                
                module_metrics[str(py_file)] = {
                    'functions': len(functions),
                    'classes': len(classes),
                    'avg_function_length': avg_function_length,
                    'is_modular': avg_function_length < 50 and len(functions) > 1
                }
                
            except Exception as e:
                self.issues['modularity_errors'].append(f"{py_file}: {e}")
                
        return module_metrics
    
    def analyze_apis(self) -> Dict:
        """Analyze API endpoints and structure"""
        api_patterns = [
            r'@app\.route\(',
            r'@router\.(get|post|put|delete|patch)',
            r'@api\.(get|post|put|delete|patch)',
            r'path\([\'"]([^\'"])+[\'"]'
        ]
        
        endpoints = defaultdict(list)
        
        for py_file in self.project_path.rglob('*.py'):
            try:
                with open(py_file, 'r', encoding='utf-8') as f:
                    content = f.read()
                    
                for pattern in api_patterns:
                    matches = re.finditer(pattern, content)
                    for match in matches:
                        line_no = content[:match.start()].count('\n') + 1
                        endpoints[str(py_file)].append({
                            'line': line_no,
                            'endpoint': match.group()
                        })
                        
            except Exception as e:
                self.issues['api_errors'].append(f"{py_file}: {e}")
                
        return {
            'endpoints': dict(endpoints),
            'total_endpoints': sum(len(v) for v in endpoints.values())
        }
    
    def security_scan(self) -> Dict:
        """Basic security vulnerability scan"""
        security_patterns = {
            'hardcoded_password': r'password\s*=\s*[\'"][^\'"]+[\'"]',
            'sql_injection': r'(SELECT|INSERT|UPDATE|DELETE).+%s',
            'eval_usage': r'\beval\s*\(',
            'exec_usage': r'\bexec\s*\(',
            'pickle_load': r'pickle\.load',
            'hardcoded_secret': r'(secret|key|token)\s*=\s*[\'"][^\'"]+[\'"]'
        }
        
        vulnerabilities = defaultdict(list)
        
        for py_file in self.project_path.rglob('*.py'):
            try:
                with open(py_file, 'r', encoding='utf-8') as f:
                    content = f.read()
                    
                for vuln_type, pattern in security_patterns.items():
                    matches = re.finditer(pattern, content, re.IGNORECASE)
                    for match in matches:
                        line_no = content[:match.start()].count('\n') + 1
                        vulnerabilities[vuln_type].append({
                            'file': str(py_file),
                            'line': line_no,
                            'code': match.group()[:50] + '...'
                        })
                        
            except Exception as e:
                self.issues['security_errors'].append(f"{py_file}: {e}")
                
        return dict(vulnerabilities)
    
    def performance_analysis(self) -> Dict:
        """Analyze potential performance issues"""
        perf_issues = defaultdict(list)
        
        patterns = {
            'nested_loops': r'for\s+.+:\s*\n\s*for\s+.+:',
            'large_list_comp': r'\[.+for.+for.+\]',
            'no_generator': r'return\s+\[.+for.+in.+\]',
            'string_concatenation': r'(\+=|\+\s*=)\s*[\'"]'
        }
        
        for py_file in self.project_path.rglob('*.py'):
            try:
                with open(py_file, 'r', encoding='utf-8') as f:
                    content = f.read()
                    
                for issue_type, pattern in patterns.items():
                    matches = re.finditer(pattern, content)
                    for match in matches:
                        line_no = content[:match.start()].count('\n') + 1
                        perf_issues[issue_type].append({
                            'file': str(py_file),
                            'line': line_no
                        })
                        
            except Exception as e:
                self.issues['performance_errors'].append(f"{py_file}: {e}")
                
        return dict(perf_issues)
    
    def _get_function_signature(self, node: ast.FunctionDef) -> str:
        """Extract function signature for comparison"""
        args = [arg.arg for arg in node.args.args]
        return f"{node.name}({','.join(args)})"
    
    def _find_callback_consolidation(self, callbacks: Dict) -> List[str]:
        """Identify opportunities for callback consolidation"""
        opportunities = []
        
        # Group by similar patterns
        pattern_groups = defaultdict(list)
        for file, cbs in callbacks.items():
            for cb in cbs:
                pattern_groups[cb['pattern']].append(file)
                
        for pattern, files in pattern_groups.items():
            if len(set(files)) > 2:
                opportunities.append(
                    f"Pattern '{pattern}' appears in {len(set(files))} files - consider consolidation"
                )
                
        return opportunities
    
    def generate_report(self, results: Dict) -> str:
        """Generate a comprehensive report"""
        report = []
        report.append("# Automated Code Review Report\n")
        report.append(f"Project: {self.project_path}")
        
        # Count total files analyzed
        py_files = list(self.project_path.rglob('*.py'))
        report.append(f"Files analyzed: {len(py_files)}\n")
        
        # Redundancy Section
        report.append("\n## Code Redundancy Analysis")
        duplicates = results['redundancy']['duplicates']
        total_functions = results['redundancy'].get('total_functions', 0)
        report.append(f"Total functions analyzed: {total_functions}")
        if duplicates:
            report.append(f"Found {len(duplicates)} duplicate function signatures:")
            for sig, locations in list(duplicates.items())[:5]:
                report.append(f"  - {sig}: {len(locations)} occurrences")
                for loc in locations[:2]:
                    report.append(f"    • {loc['file']}:{loc['line']}")
        else:
            report.append("✓ No duplicate functions found")
        
        # Modularity Section
        report.append("\n## Modularity Assessment")
        mod_data = results.get('modularity', {})
        if mod_data:
            modular_files = sum(1 for f in mod_data.values() if f.get('is_modular', False))
            report.append(f"Modular files: {modular_files}/{len(mod_data)}")
            
            # Find files with long functions
            long_functions = [(f, d['avg_function_length']) 
                            for f, d in mod_data.items() 
                            if d['avg_function_length'] > 50]
            if long_functions:
                report.append("Files with long functions (>50 lines):")
                for file, avg_len in sorted(long_functions, key=lambda x: x[1], reverse=True)[:5]:
                    report.append(f"  - {file}: avg {avg_len:.1f} lines/function")
        
        # Callbacks Section
        report.append("\n## Callback Analysis")
        report.append(f"Total callbacks found: {results['callbacks']['total_callbacks']}")
        if results['callbacks']['callbacks_found']:
            report.append("Callback distribution:")
            for file, cbs in list(results['callbacks']['callbacks_found'].items())[:5]:
                report.append(f"  - {file}: {len(cbs)} callbacks")
        for opp in results['callbacks']['consolidation_opportunities'][:3]:
            report.append(f"  - {opp}")
        
        # Unicode Section
        report.append("\n## Unicode Handling")
        unicode_issues = results['unicode_issues']['issues']
        report.append(f"Found {len(unicode_issues)} potential encoding issues")
        if unicode_issues:
            for issue in unicode_issues[:5]:
                report.append(f"  - {issue['file']}:{issue['line']} - {issue['issue']}")
        good_files = results['unicode_issues'].get('files_with_proper_handling', [])
        if good_files:
            report.append(f"✓ {len(good_files)} files use proper UTF-8 encoding")
        
        # Python 3 Compliance
        report.append("\n## Python 3 Compliance")
        if results['python3_compliance']['is_compliant']:
            report.append("✓ Code is Python 3 compliant")
        else:
            report.append("✗ Found Python 2 code that needs updating:")
            py2_issues = results['python3_compliance']['python2_code_found']
            for file, issues in list(py2_issues.items())[:5]:
                report.append(f"  - {file}:")
                for issue in issues[:3]:
                    report.append(f"    • Line {issue['line']}: {issue['type']} - {issue['code']}")
        
        # API Analysis
        report.append("\n## API Analysis")
        total_endpoints = results['api_analysis']['total_endpoints']
        report.append(f"Total API endpoints found: {total_endpoints}")
        if results['api_analysis']['endpoints']:
            report.append("API files:")
            for file, endpoints in list(results['api_analysis']['endpoints'].items())[:5]:
                report.append(f"  - {file}: {len(endpoints)} endpoints")
        
        # Security Issues
        report.append("\n## Security Scan Results")
        security_issues = results.get('security_issues', {})
        total_security_issues = sum(len(issues) for issues in security_issues.values())
        if total_security_issues > 0:
            report.append(f"⚠️  Found {total_security_issues} potential security issues:")
            for vuln_type, issues in security_issues.items():
                if issues:
                    report.append(f"  - {vuln_type}: {len(issues)} instances")
                    for issue in issues[:2]:
                        report.append(f"    • {issue['file']}:{issue['line']}")
        else:
            report.append("✓ No obvious security issues detected")
        
        # Performance Issues
        report.append("\n## Performance Analysis")
        perf_issues = results.get('performance_issues', {})
        total_perf_issues = sum(len(issues) for issues in perf_issues.values())
        if total_perf_issues > 0:
            report.append(f"Found {total_perf_issues} potential performance issues:")
            for issue_type, issues in perf_issues.items():
                if issues:
                    report.append(f"  - {issue_type}: {len(issues)} instances")
        else:
            report.append("✓ No obvious performance issues detected")
        
        # Summary
        report.append("\n## Summary")
        report.append(f"- Files analyzed: {len(py_files)}")
        report.append(f"- Total functions: {total_functions}")
        report.append(f"- Duplicate functions: {len(duplicates)}")
        report.append(f"- Security issues: {total_security_issues}")
        report.append(f"- Performance issues: {total_perf_issues}")
        report.append(f"- Python 3 compliant: {'Yes' if results['python3_compliance']['is_compliant'] else 'No'}")
        
        return '\n'.join(report)


def main():
    """Run the code analyzer"""
    import sys
    
    if len(sys.argv) != 2:
        print("Usage: python3 code_analyzer.py <project_path>")
        print("Example: python3 code_analyzer.py .")
        print("         python3 code_analyzer.py /Users/username/projects/yosai_intel_dashboard_fresh")
        sys.exit(1)
    
    project_path = Path(sys.argv[1])
    
    # Validate path exists
    if not project_path.exists():
        print(f"Error: Path '{project_path}' does not exist!")
        sys.exit(1)
    
    if not project_path.is_dir():
        print(f"Error: '{project_path}' is not a directory!")
        sys.exit(1)
    
    # Check for Python files
    py_files = list(project_path.rglob('*.py'))
    if not py_files:
        print(f"Error: No Python files found in '{project_path}'")
        print("Make sure you're pointing to the correct directory containing .py files")
        sys.exit(1)
    
    print(f"Found {len(py_files)} Python files in {project_path}")
    print("Starting code analysis...")
    
    analyzer = CodeAnalyzer(project_path)
    results = analyzer.analyze_project()
    
    # Save detailed results
    with open('code_review_results.json', 'w') as f:
        json.dump(results, f, indent=2, default=str)
    
    # Generate and print report
    report = analyzer.generate_report(results)
    print(report)
    
    with open('code_review_report.md', 'w') as f:
        f.write(report)
    
    print("\nDetailed results saved to: code_review_results.json")
    print("Report saved to: code_review_report.md")
    
    # Print summary of issues found
    if analyzer.issues:
        print("\n⚠️  Issues encountered during analysis:")
        for issue_type, issues in analyzer.issues.items():
            print(f"  - {issue_type}: {len(issues)} issues")


if __name__ == "__main__":
    main()