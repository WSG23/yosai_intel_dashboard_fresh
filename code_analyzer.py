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
    
    def find_redundant_code(self) -> Dict:
        """Identify duplicate and redundant code blocks"""
        duplicates = defaultdict(list)
        function_signatures = defaultdict(list)
        
        for py_file in self.project_path.rglob('*.py'):
            try:
                with open(py_file, 'r', encoding='utf-8') as f:
                    tree = ast.parse(f.read())
                    
                for node in ast.walk(tree):
                    if isinstance(node, ast.FunctionDef):
                        # Create function signature
                        sig = self._get_function_signature(node)
                        function_signatures[sig].append({
                            'file': str(py_file),
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
        report.append(f"Project: {self.project_path}\n")
        
        # Redundancy Section
        report.append("\n## Code Redundancy Analysis")
        duplicates = results['redundancy']['duplicates']
        if duplicates:
            report.append(f"Found {len(duplicates)} duplicate function signatures:")
            for sig, locations in list(duplicates.items())[:5]:
                report.append(f"  - {sig}: {len(locations)} occurrences")
        
        # Callbacks Section
        report.append("\n## Callback Analysis")
        report.append(f"Total callbacks found: {results['callbacks']['total_callbacks']}")
        for opp in results['callbacks']['consolidation_opportunities'][:3]:
            report.append(f"  - {opp}")
        
        # Unicode Section
        report.append("\n## Unicode Handling")
        unicode_issues = results['unicode_issues']['issues']
        report.append(f"Found {len(unicode_issues)} potential encoding issues")
        
        # Python 3 Compliance
        report.append("\n## Python 3 Compliance")
        if results['python3_compliance']['is_compliant']:
            report.append("✓ Code is Python 3 compliant")
        else:
            report.append("✗ Found Python 2 code that needs updating")
        
        # Security Issues
        report.append("\n## Security Scan Results")
        for vuln_type, issues in results['security_issues'].items():
            if issues:
                report.append(f"  - {vuln_type}: {len(issues)} instances")
        
        return '\n'.join(report)


def main():
    """Run the code analyzer"""
    import sys
    
    if len(sys.argv) != 2:
        print("Usage: python code_analyzer.py <project_path>")
        sys.exit(1)
    
    project_path = sys.argv[1]
    analyzer = CodeAnalyzer(project_path)
    
    print("Starting code analysis...")
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


if __name__ == "__main__":
    main()