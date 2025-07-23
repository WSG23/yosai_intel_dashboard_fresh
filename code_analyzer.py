#!/usr/bin/env python3
"""
Improved Code Analyzer for Yosai Intel Dashboard
Handles mixed JS/TS/Python projects with proper exclusions
"""

import ast
import os
import re
from pathlib import Path
from typing import Dict, List, Set, Tuple, Optional
from collections import defaultdict, Counter
import json
import time


class ImprovedCodeAnalyzer:
    """Analyzes Python code in mixed-language projects"""
    
    def __init__(self, project_path: str):
        self.project_path = Path(project_path)
        self.issues = defaultdict(list)
        self.metrics = {}
        # Directories to exclude from analysis
        self.exclude_dirs = {
            '.git', 'node_modules', '__pycache__', '.pytest_cache', 
            'venv', 'env', '.venv', 'dist', 'build', '.next',
            '.idea', '.vscode', 'coverage', 'htmlcov'
        }
        self.python_files = []
        self.project_stats = {}
        
    def _get_python_files(self) -> List[Path]:
        """Get all Python files, excluding certain directories"""
        if self.python_files:  # Cache the result
            return self.python_files
            
        python_files = []
        excluded_count = 0
        
        for py_file in self.project_path.rglob('*.py'):
            # Skip files in excluded directories
            if any(excluded in py_file.parts for excluded in self.exclude_dirs):
                excluded_count += 1
                continue
            python_files.append(py_file)
        
        self.python_files = python_files
        self.project_stats['excluded_python_files'] = excluded_count
        return python_files
    
    def analyze_project_structure(self) -> Dict:
        """Analyze overall project structure"""
        print("📊 Analyzing project structure...")
        
        file_types = Counter()
        python_locations = defaultdict(int)
        
        for file_path in self.project_path.rglob('*'):
            if file_path.is_file():
                if any(excluded in file_path.parts for excluded in self.exclude_dirs):
                    continue
                    
                ext = file_path.suffix.lower()
                file_types[ext] += 1
                
                if ext == '.py':
                    # Track where Python files are located
                    if file_path.parent == self.project_path:
                        python_locations['root'] += 1
                    else:
                        top_dir = file_path.relative_to(self.project_path).parts[0]
                        python_locations[top_dir] += 1
        
        return {
            'file_types': dict(file_types.most_common(10)),
            'python_distribution': dict(python_locations),
            'is_mixed_language': file_types['.js'] > 0 or file_types['.ts'] > 0,
            'primary_language': 'JavaScript/TypeScript' if file_types['.js'] + file_types['.ts'] > file_types['.py'] else 'Python'
        }
    
    def analyze_project(self) -> Dict:
        """Run complete analysis on the project"""
        start_time = time.time()
        
        print(f"\n🔍 Analyzing Python code in: {self.project_path}")
        print(f"   Excluding: {', '.join(sorted(self.exclude_dirs))}")
        
        # Get Python files first
        python_files = self._get_python_files()
        print(f"   Found {len(python_files)} Python files to analyze")
        
        if not python_files:
            return {'error': 'No Python files found to analyze'}
        
        results = {
            'project_info': {
                'path': str(self.project_path),
                'python_files_analyzed': len(python_files),
                'excluded_files': self.project_stats.get('excluded_python_files', 0),
                'analysis_time': 0  # Will be updated at end
            },
            'project_structure': self.analyze_project_structure(),
            'redundancy': self.find_redundant_code(),
            'callbacks': self.analyze_callbacks(),
            'unicode_issues': self.check_unicode_handling(),
            'python3_compliance': self.check_python3_compliance(),
            'modularity': self.assess_modularity(),
            'api_analysis': self.analyze_apis(),
            'security_issues': self.security_scan(),
            'performance_issues': self.performance_analysis(),
            'code_quality': self.analyze_code_quality()
        }
        
        # Add analysis time
        results['project_info']['analysis_time'] = round(time.time() - start_time, 2)
        
        return results
    
    def find_redundant_code(self) -> Dict:
        """Identify duplicate and redundant code blocks"""
        print("🔄 Finding redundant code...")
        
        duplicates = defaultdict(list)
        function_signatures = defaultdict(list)
        import_patterns = defaultdict(int)
        
        for py_file in self._get_python_files():
            try:
                with open(py_file, 'r', encoding='utf-8') as f:
                    content = f.read()
                    tree = ast.parse(content)
                    
                # Analyze imports
                for node in ast.walk(tree):
                    if isinstance(node, ast.Import):
                        for alias in node.names:
                            import_patterns[alias.name] += 1
                    elif isinstance(node, ast.ImportFrom):
                        if node.module:
                            import_patterns[node.module] += 1
                    
                # Analyze functions
                for node in ast.walk(tree):
                    if isinstance(node, ast.FunctionDef):
                        sig = self._get_function_signature(node)
                        rel_path = py_file.relative_to(self.project_path)
                        function_signatures[sig].append({
                            'file': str(rel_path),
                            'line': node.lineno,
                            'name': node.name,
                            'size': node.end_lineno - node.lineno if node.end_lineno else 0
                        })
            except Exception as e:
                self.issues['parse_errors'].append(f"{py_file}: {e}")
        
        # Find duplicates
        for sig, locations in function_signatures.items():
            if len(locations) > 1:
                duplicates[sig] = locations
        
        # Find most common imports
        common_imports = sorted(import_patterns.items(), key=lambda x: x[1], reverse=True)[:20]
        
        return {
            'duplicates': dict(duplicates),
            'total_functions': sum(len(v) for v in function_signatures.values()),
            'duplicate_functions': len(duplicates),
            'common_imports': common_imports,
            'potential_savings': sum(loc['size'] for locs in duplicates.values() for loc in locs[1:])
        }
    
    def analyze_callbacks(self) -> Dict:
        """Find and analyze callback patterns"""
        print("📞 Analyzing callbacks...")
        
        callbacks = defaultdict(list)
        callback_patterns = [
            (r'callback\s*=', 'callback assignment'),
            (r'on[A-Z]\w+\s*=', 'event handler'),
            (r'\.subscribe\(', 'subscription'),
            (r'\.then\(', 'promise then'),
            (r'addEventListener\(', 'event listener'),
            (r'@\w+\.callback', 'decorator callback'),
            (r'register_callback\(', 'callback registration')
        ]
        
        for py_file in self._get_python_files():
            try:
                with open(py_file, 'r', encoding='utf-8') as f:
                    content = f.read()
                    
                for pattern, pattern_type in callback_patterns:
                    matches = re.finditer(pattern, content)
                    for match in matches:
                        line_no = content[:match.start()].count('\n') + 1
                        rel_path = py_file.relative_to(self.project_path)
                        callbacks[str(rel_path)].append({
                            'pattern': pattern,
                            'type': pattern_type,
                            'line': line_no,
                            'context': content[max(0, match.start()-30):match.end()+30].strip()
                        })
            except Exception as e:
                self.issues['callback_errors'].append(f"{py_file}: {e}")
        
        return {
            'callbacks_found': dict(callbacks),
            'total_callbacks': sum(len(v) for v in callbacks.values()),
            'consolidation_opportunities': self._find_callback_consolidation(callbacks),
            'callback_types': self._categorize_callbacks(callbacks)
        }
    
    def check_unicode_handling(self) -> Dict:
        """Check for proper Unicode and UTF-8 handling"""
        print("🌐 Checking Unicode handling...")
        
        unicode_issues = []
        proper_handling = []
        encoding_declarations = 0
        
        patterns = {
            'good': [
                r'encoding\s*=\s*[\'"]utf-?8[\'"]',
                r'\.encode\([\'"]utf-?8[\'"]',
                r'\.decode\([\'"]utf-?8[\'"]',
                r'# -\*- coding: utf-?8 -\*-',
                r'errors\s*=\s*[\'"](?:ignore|replace|surrogateescape)[\'"]'
            ],
            'bad': [
                r'\.encode\(\s*\)',
                r'\.decode\(\s*\)',
                r'str\([^,)]+\)',  # str() without encoding
                r'unicode\(',      # Python 2 style
            ],
            'risky': [
                r'open\([^,)]+\)',  # open() without encoding
                r'codecs\.open\([^,)]+,[^,)]+\)',  # codecs without encoding
            ]
        }
        
        for py_file in self._get_python_files():
            try:
                with open(py_file, 'r', encoding='utf-8') as f:
                    content = f.read()
                    lines = content.splitlines()
                    
                # Check for encoding declaration
                if lines and ('coding' in lines[0] or 'coding' in (lines[1] if len(lines) > 1 else '')):
                    encoding_declarations += 1
                    
                rel_path = py_file.relative_to(self.project_path)
                
                for pattern in patterns['bad']:
                    matches = re.finditer(pattern, content)
                    for match in matches:
                        line_no = content[:match.start()].count('\n') + 1
                        unicode_issues.append({
                            'file': str(rel_path),
                            'line': line_no,
                            'issue': f"Potential encoding issue: {match.group()[:30]}",
                            'severity': 'high'
                        })
                
                for pattern in patterns['risky']:
                    matches = re.finditer(pattern, content)
                    for match in matches:
                        line_no = content[:match.start()].count('\n') + 1
                        unicode_issues.append({
                            'file': str(rel_path),
                            'line': line_no,
                            'issue': f"Missing encoding parameter: {match.group()[:30]}",
                            'severity': 'medium'
                        })
                        
                has_good_practices = False
                for pattern in patterns['good']:
                    if re.search(pattern, content):
                        has_good_practices = True
                        break
                        
                if has_good_practices:
                    proper_handling.append(str(rel_path))
                        
            except Exception as e:
                self.issues['unicode_errors'].append(f"{py_file}: {e}")
        
        return {
            'issues': unicode_issues,
            'files_with_proper_handling': list(set(proper_handling)),
            'encoding_declarations': encoding_declarations,
            'recommendation': "Ensure all string encoding/decoding uses explicit UTF-8",
            'high_severity_count': len([i for i in unicode_issues if i.get('severity') == 'high']),
            'medium_severity_count': len([i for i in unicode_issues if i.get('severity') == 'medium'])
        }
    
    def check_python3_compliance(self) -> Dict:
        """Verify Python 3 compliance"""
        print("🐍 Checking Python 3 compliance...")
        
        py2_patterns = {
            'print_statement': r'print\s+[^(]',
            'xrange': r'\bxrange\s*\(',
            'unicode_literal': r'\bunicode\s*\(',
            'iteritems': r'\.iteritems\s*\(',
            'iterkeys': r'\.iterkeys\s*\(',
            'itervalues': r'\.itervalues\s*\(',
            'raw_input': r'\braw_input\s*\(',
            'execfile': r'\bexecfile\s*\(',
            'has_key': r'\.has_key\s*\(',
            'apply': r'\bapply\s*\(',
            'buffer': r'\bbuffer\s*\(',
            'cmp': r'\bcmp\s*\(',
            'coerce': r'\bcoerce\s*\(',
            'file_builtin': r'\bfile\s*\(',
            'long_literal': r'\b\d+[lL]\b',
            'backticks': r'`[^`]+`',
            'ne_operator': r'<>',
            'dict_methods': r'\.(?:viewkeys|viewvalues|viewitems)\s*\('
        }
        
        compliance_issues = defaultdict(list)
        
        for py_file in self._get_python_files():
            try:
                with open(py_file, 'r', encoding='utf-8') as f:
                    content = f.read()
                    
                rel_path = py_file.relative_to(self.project_path)
                    
                for name, pattern in py2_patterns.items():
                    matches = re.finditer(pattern, content)
                    for match in matches:
                        line_no = content[:match.start()].count('\n') + 1
                        compliance_issues[str(rel_path)].append({
                            'type': name,
                            'line': line_no,
                            'code': match.group()[:50]
                        })
                        
            except Exception as e:
                self.issues['py3_errors'].append(f"{py_file}: {e}")
        
        return {
            'python2_code_found': dict(compliance_issues),
            'is_compliant': len(compliance_issues) == 0,
            'total_issues': sum(len(issues) for issues in compliance_issues.values()),
            'issue_types': Counter(issue['type'] for issues in compliance_issues.values() for issue in issues)
        }
    
    def assess_modularity(self) -> Dict:
        """Assess code modularity"""
        print("📦 Assessing modularity...")
        
        module_metrics = {}
        
        for py_file in self._get_python_files():
            try:
                with open(py_file, 'r', encoding='utf-8') as f:
                    content = f.read()
                    tree = ast.parse(content)
                    
                functions = [n for n in ast.walk(tree) if isinstance(n, ast.FunctionDef)]
                classes = [n for n in ast.walk(tree) if isinstance(n, ast.ClassDef)]
                
                # Calculate metrics
                function_lengths = []
                for func in functions:
                    if func.end_lineno:
                        length = func.end_lineno - func.lineno
                        function_lengths.append(length)
                
                avg_function_length = sum(function_lengths) / len(function_lengths) if function_lengths else 0
                max_function_length = max(function_lengths) if function_lengths else 0
                
                # Count imports
                imports = len([n for n in ast.walk(tree) if isinstance(n, (ast.Import, ast.ImportFrom))])
                
                # Measure complexity (simplified)
                complexity = len(functions) + len(classes) * 2 + imports
                
                rel_path = py_file.relative_to(self.project_path)
                module_metrics[str(rel_path)] = {
                    'functions': len(functions),
                    'classes': len(classes),
                    'avg_function_length': round(avg_function_length, 1),
                    'max_function_length': max_function_length,
                    'imports': imports,
                    'complexity_score': complexity,
                    'is_modular': avg_function_length < 50 and max_function_length < 100,
                    'lines_of_code': len(content.splitlines())
                }
                
            except Exception as e:
                self.issues['modularity_errors'].append(f"{py_file}: {e}")
        
        # Calculate aggregates
        all_metrics = list(module_metrics.values())
        return {
            'file_metrics': module_metrics,
            'summary': {
                'total_functions': sum(m['functions'] for m in all_metrics),
                'total_classes': sum(m['classes'] for m in all_metrics),
                'avg_file_complexity': sum(m['complexity_score'] for m in all_metrics) / len(all_metrics) if all_metrics else 0,
                'modular_files': sum(1 for m in all_metrics if m['is_modular']),
                'total_lines_of_code': sum(m['lines_of_code'] for m in all_metrics)
            }
        }
    
    def analyze_apis(self) -> Dict:
        """Analyze API endpoints and structure"""
        print("🌐 Analyzing APIs...")
        
        api_patterns = [
            # Flask patterns
            (r'@app\.route\([\'"]([^\'"])+[\'"]\)', 'flask'),
            (r'@blueprint\.route\([\'"]([^\'"])+[\'"]\)', 'flask_blueprint'),
            # FastAPI patterns
            (r'@app\.(get|post|put|delete|patch)\([\'"]([^\'"])+[\'"]\)', 'fastapi'),
            (r'@router\.(get|post|put|delete|patch)\([\'"]([^\'"])+[\'"]\)', 'fastapi_router'),
            # Django patterns
            (r'path\([\'"]([^\'"])+[\'"]', 'django'),
            (r'url\(r[\'"]\^([^\'"])+\$?[\'"]', 'django_legacy'),
            # Generic REST patterns
            (r'@api\.(get|post|put|delete|patch)', 'generic_api'),
            (r'\.add_route\([\'"]([^\'"])+[\'"]', 'generic_route')
        ]
        
        endpoints = defaultdict(list)
        api_frameworks = set()
        
        for py_file in self._get_python_files():
            try:
                with open(py_file, 'r', encoding='utf-8') as f:
                    content = f.read()
                    
                rel_path = py_file.relative_to(self.project_path)
                    
                for pattern, framework in api_patterns:
                    matches = re.finditer(pattern, content)
                    for match in matches:
                        api_frameworks.add(framework)
                        line_no = content[:match.start()].count('\n') + 1
                        
                        # Try to extract the endpoint path
                        endpoint_match = re.search(r'[\'"]([^\'"]+)[\'"]', match.group())
                        endpoint_path = endpoint_match.group(1) if endpoint_match else 'unknown'
                        
                        endpoints[str(rel_path)].append({
                            'line': line_no,
                            'endpoint': endpoint_path,
                            'framework': framework,
                            'full_match': match.group()[:100]
                        })
                        
            except Exception as e:
                self.issues['api_errors'].append(f"{py_file}: {e}")
        
        # Group endpoints by path
        all_endpoints = []
        for file_endpoints in endpoints.values():
            all_endpoints.extend([e['endpoint'] for e in file_endpoints])
        
        endpoint_counts = Counter(all_endpoints)
        
        return {
            'endpoints': dict(endpoints),
            'total_endpoints': sum(len(v) for v in endpoints.values()),
            'frameworks_detected': list(api_frameworks),
            'duplicate_endpoints': {k: v for k, v in endpoint_counts.items() if v > 1},
            'api_files': len(endpoints)
        }
    
    def security_scan(self) -> Dict:
        """Basic security vulnerability scan"""
        print("🔒 Running security scan...")
        
        security_patterns = {
            'hardcoded_password': (r'(?:password|passwd|pwd)\s*=\s*[\'"][^\'"]{4,}[\'"]', 'high'),
            'hardcoded_secret': (r'(?:secret|key|token|api_key)\s*=\s*[\'"][^\'"]{8,}[\'"]', 'high'),
            'sql_injection': (r'(?:SELECT|INSERT|UPDATE|DELETE|DROP|UNION).+[\'"]?\s*\+\s*\w+|%s|format\(|f[\'"].*{', 'high'),
            'eval_usage': (r'\beval\s*\(', 'high'),
            'exec_usage': (r'\bexec\s*\(', 'high'),
            'pickle_load': (r'pickle\.(?:load|loads)\s*\(', 'medium'),
            'yaml_load': (r'yaml\.(?:load|load_all)\s*\((?!.*Loader)', 'medium'),
            'shell_injection': (r'(?:subprocess|os)\.\w+\(.*shell\s*=\s*True', 'high'),
            'weak_random': (r'random\.(?:random|randint|choice)\s*\(', 'low'),
            'md5_usage': (r'hashlib\.md5\s*\(', 'medium'),
            'debug_enabled': (r'DEBUG\s*=\s*True', 'medium'),
            'cors_wildcard': (r'Access-Control-Allow-Origin.*\*', 'medium'),
            'unvalidated_redirect': (r'redirect\([^)]*request\.[^)]+\)', 'medium')
        }
        
        vulnerabilities = defaultdict(list)
        
        for py_file in self._get_python_files():
            try:
                with open(py_file, 'r', encoding='utf-8') as f:
                    content = f.read()
                    
                rel_path = py_file.relative_to(self.project_path)
                    
                for vuln_type, (pattern, severity) in security_patterns.items():
                    matches = re.finditer(pattern, content, re.IGNORECASE)
                    for match in matches:
                        line_no = content[:match.start()].count('\n') + 1
                        
                        # Don't flag test files for some patterns
                        if 'test' in str(rel_path).lower() and vuln_type in ['hardcoded_password', 'debug_enabled']:
                            continue
                            
                        vulnerabilities[vuln_type].append({
                            'file': str(rel_path),
                            'line': line_no,
                            'severity': severity,
                            'code': match.group()[:50] + '...' if len(match.group()) > 50 else match.group()
                        })
                        
            except Exception as e:
                self.issues['security_errors'].append(f"{py_file}: {e}")
        
        # Calculate severity summary
        severity_summary = defaultdict(int)
        for vuln_list in vulnerabilities.values():
            for vuln in vuln_list:
                severity_summary[vuln['severity']] += 1
        
        return {
            **dict(vulnerabilities),
            'severity_summary': dict(severity_summary),
            'total_issues': sum(len(v) for v in vulnerabilities.values())
        }
    
    def performance_analysis(self) -> Dict:
        """Analyze potential performance issues"""
        print("⚡ Analyzing performance...")
        
        perf_issues = defaultdict(list)
        
        patterns = {
            'nested_loops': (r'for\s+.+:\s*\n\s+for\s+.+:', 'Nested loops detected'),
            'large_list_comp': (r'\[.{50,}for.+for.+\]', 'Complex list comprehension'),
            'no_generator': (r'return\s+\[.+for.+in.+\]', 'Could use generator'),
            'string_concatenation': (r'[\+\s]*=\s*[\'"][^\'"]*[\'"](?:\s*\+|$)', 'String concatenation in loop'),
            'repeated_regex': (r're\.(compile|search|match|findall)\([\'"][^\'"]+[\'"]', 'Regex not compiled'),
            'global_lookup': (r'global\s+\w+', 'Global variable usage'),
            'inefficient_contains': (r'if\s+.+\s+in\s+.+\.keys\(\)', 'Inefficient "in dict.keys()"'),
            'repeated_append': (r'\.append\(.+\).*\.append\(.+\)', 'Multiple appends')
        }
        
        for py_file in self._get_python_files():
            try:
                with open(py_file, 'r', encoding='utf-8') as f:
                    content = f.read()
                    
                rel_path = py_file.relative_to(self.project_path)
                    
                for issue_type, (pattern, description) in patterns.items():
                    matches = re.finditer(pattern, content, re.MULTILINE | re.DOTALL)
                    for match in matches:
                        line_no = content[:match.start()].count('\n') + 1
                        perf_issues[issue_type].append({
                            'file': str(rel_path),
                            'line': line_no,
                            'description': description
                        })
                        
            except Exception as e:
                self.issues['performance_errors'].append(f"{py_file}: {e}")
        
        return dict(perf_issues)
    
    def analyze_code_quality(self) -> Dict:
        """Additional code quality metrics"""
        print("📏 Analyzing code quality...")
        
        quality_metrics = {
            'files_with_docstrings': 0,
            'files_with_type_hints': 0,
            'files_with_tests': 0,
            'average_file_size': 0,
            'largest_files': []
        }
        
        file_sizes = []
        
        for py_file in self._get_python_files():
            try:
                with open(py_file, 'r', encoding='utf-8') as f:
                    content = f.read()
                    lines = len(content.splitlines())
                    
                file_sizes.append((str(py_file.relative_to(self.project_path)), lines))
                
                # Check for docstrings
                if '"""' in content or "'''" in content:
                    quality_metrics['files_with_docstrings'] += 1
                
                # Check for type hints
                if '->' in content or ': ' in content and 'def ' in content:
                    quality_metrics['files_with_type_hints'] += 1
                
                # Check if it's a test file
                if 'test_' in py_file.name or '_test.py' in str(py_file):
                    quality_metrics['files_with_tests'] += 1
                    
            except Exception as e:
                self.issues['quality_errors'].append(f"{py_file}: {e}")
        
        # Calculate metrics
        if file_sizes:
            quality_metrics['average_file_size'] = sum(size for _, size in file_sizes) / len(file_sizes)
            quality_metrics['largest_files'] = sorted(file_sizes, key=lambda x: x[1], reverse=True)[:10]
        
        return quality_metrics
    
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
                pattern_groups[cb['type']].append(file)
        
        for pattern_type, files in pattern_groups.items():
            unique_files = len(set(files))
            if unique_files > 2:
                opportunities.append(
                    f"{pattern_type} appears in {unique_files} files - consider consolidation"
                )
        
        return opportunities
    
    def _categorize_callbacks(self, callbacks: Dict) -> Dict[str, int]:
        """Categorize callbacks by type"""
        categories = defaultdict(int)
        
        for file_callbacks in callbacks.values():
            for cb in file_callbacks:
                categories[cb['type']] += 1
        
        return dict(categories)
    
    def generate_report(self, results: Dict) -> str:
        """Generate a comprehensive report"""
        report = []
        report.append("# Comprehensive Python Code Review Report\n")
        report.append(f"Project: {results['project_info']['path']}")
        report.append(f"Analysis completed in: {results['project_info']['analysis_time']}s")
        
        # Project overview
        proj_struct = results['project_structure']
        report.append(f"\n## Project Overview")
        report.append(f"- Primary Language: {proj_struct['primary_language']}")
        report.append(f"- Python files analyzed: {results['project_info']['python_files_analyzed']}")
        report.append(f"- Excluded files: {results['project_info']['excluded_files']}")
        if proj_struct['is_mixed_language']:
            report.append("- Mixed-language project detected (JS/TS + Python)")
        
        # Python distribution
        report.append("\n### Python Code Distribution:")
        for location, count in sorted(proj_struct['python_distribution'].items(), key=lambda x: x[1], reverse=True)[:10]:
            report.append(f"  - {location}: {count} files")
        
        # Code redundancy
        report.append(f"\n## Code Redundancy Analysis")
        redundancy = results['redundancy']
        report.append(f"Total functions analyzed: {redundancy['total_functions']}")
        report.append(f"Duplicate functions found: {redundancy['duplicate_functions']}")
        if redundancy.get('potential_savings', 0) > 0:
            report.append(f"Potential lines saved by removing duplicates: {redundancy['potential_savings']}")
        
        # Top duplicates
        if redundancy['duplicates']:
            report.append("\nMost duplicated functions:")
            sorted_dupes = sorted(redundancy['duplicates'].items(), 
                                key=lambda x: len(x[1]), reverse=True)[:5]
            for sig, locations in sorted_dupes:
                report.append(f"  - {sig}: {len(locations)} occurrences")
                for loc in locations[:2]:
                    report.append(f"    • {loc['file']}:{loc['line']}")
        
        # Modularity
        modularity = results['modularity']
        summary = modularity['summary']
        report.append(f"\n## Code Modularity")
        report.append(f"- Total functions: {summary['total_functions']}")
        report.append(f"- Total classes: {summary['total_classes']}")
        report.append(f"- Total lines of code: {summary['total_lines_of_code']:,}")
        report.append(f"- Modular files: {summary['modular_files']}/{len(modularity['file_metrics'])}")
        
        # Callbacks
        callbacks = results['callbacks']
        report.append(f"\n## Callback Analysis")
        report.append(f"Total callbacks found: {callbacks['total_callbacks']}")
        if callbacks['callback_types']:
            report.append("Callback types:")
            for cb_type, count in sorted(callbacks['callback_types'].items(), 
                                       key=lambda x: x[1], reverse=True):
                report.append(f"  - {cb_type}: {count}")
        
        # Unicode handling
        unicode_data = results['unicode_issues']
        report.append(f"\n## Unicode Handling")
        report.append(f"High severity issues: {unicode_data['high_severity_count']}")
        report.append(f"Medium severity issues: {unicode_data['medium_severity_count']}")
        report.append(f"Files with proper UTF-8 handling: {len(unicode_data['files_with_proper_handling'])}")
        
        # Python 3 compliance
        py3 = results['python3_compliance']
        report.append(f"\n## Python 3 Compliance")
        if py3['is_compliant']:
            report.append("✅ Code is Python 3 compliant")
        else:
            report.append(f"❌ Found {py3['total_issues']} Python 2 compatibility issues")
            if py3['issue_types']:
                report.append("Issue breakdown:")
                for issue_type, count in py3['issue_types'].most_common(5):
                    report.append(f"  - {issue_type}: {count}")
        
        # API Analysis
        apis = results['api_analysis']
        report.append(f"\n## API Analysis")
        report.append(f"Total endpoints: {apis['total_endpoints']}")
        report.append(f"API files: {apis['api_files']}")
        if apis['frameworks_detected']:
            report.append(f"Frameworks: {', '.join(apis['frameworks_detected'])}")
        if apis['duplicate_endpoints']:
            report.append(f"Duplicate endpoints found: {len(apis['duplicate_endpoints'])}")
        
        # Security
        security = results['security_issues']
        report.append(f"\n## Security Scan")
        report.append(f"Total security issues: {security.get('total_issues', 0)}")
        if security.get('severity_summary'):
            for severity, count in sorted(security['severity_summary'].items()):
                report.append(f"  - {severity.upper()} severity: {count}")
        
        # Performance
        perf = results['performance_issues']
        total_perf_issues = sum(len(issues) for issues in perf.values() if isinstance(issues, list))
        report.append(f"\n## Performance Analysis")
        report.append(f"Total performance issues: {total_perf_issues}")
        
        # Code quality
        quality = results['code_quality']
        report.append(f"\n## Code Quality Metrics")
        report.append(f"- Files with docstrings: {quality['files_with_docstrings']}")
        report.append(f"- Files with type hints: {quality['files_with_type_hints']}")
        report.append(f"- Test files found: {quality['files_with_tests']}")
        report.append(f"- Average file size: {quality['average_file_size']:.1f} lines")
        
        # Summary and recommendations
        report.append(f"\n## Summary & Recommendations")
        
        # Critical issues
        critical_issues = []
        if security.get('total_issues', 0) > 0:
            critical_issues.append(f"Fix {security['total_issues']} security vulnerabilities")
        if not py3['is_compliant']:
            critical_issues.append(f"Migrate {py3['total_issues']} Python 2 code instances")
        if redundancy['duplicate_functions'] > 50:
            critical_issues.append(f"Eliminate {redundancy['duplicate_functions']} duplicate functions")
        
        if critical_issues:
            report.append("\n### 🚨 Critical Issues:")
            for issue in critical_issues:
                report.append(f"- {issue}")
        
        # Improvements
        improvements = []
        if unicode_data['high_severity_count'] > 0:
            improvements.append("Fix Unicode handling issues")
        if quality['files_with_docstrings'] < len(self._get_python_files()) * 0.5:
            improvements.append("Add docstrings to more files")
        if quality['files_with_type_hints'] < len(self._get_python_files()) * 0.3:
            improvements.append("Add type hints for better code clarity")
        
        if improvements:
            report.append("\n### 📈 Recommended Improvements:")
            for improvement in improvements:
                report.append(f"- {improvement}")
        
        return '\n'.join(report)


def main():
    """Run the improved code analyzer"""
    import sys
    import argparse
    
    parser = argparse.ArgumentParser(description='Analyze Python code in mixed-language projects')
    parser.add_argument('project_path', help='Path to the project directory')
    parser.add_argument('--output', '-o', default='improved_analysis', 
                       help='Output filename prefix (default: improved_analysis)')
    
    args = parser.parse_args()
    
    project_path = Path(args.project_path)
    
    # Validate path
    if not project_path.exists():
        print(f"❌ Error: Path '{project_path}' does not exist!")
        sys.exit(1)
    
    if not project_path.is_dir():
        print(f"❌ Error: '{project_path}' is not a directory!")
        sys.exit(1)
    
    # Run analysis
    analyzer = ImprovedCodeAnalyzer(project_path)
    results = analyzer.analyze_project()
    
    # Save detailed results
    json_file = f'{args.output}_results.json'
    with open(json_file, 'w') as f:
        json.dump(results, f, indent=2, default=str)
    
    # Generate and save report
    report = analyzer.generate_report(results)
    
    # Print report
    print("\n" + "="*60)
    print(report)
    print("="*60)
    
    # Save report
    report_file = f'{args.output}_report.md'
    with open(report_file, 'w') as f:
        f.write(report)
    
    print(f"\n✅ Analysis complete!")
    print(f"📊 Detailed results saved to: {json_file}")
    print(f"📄 Report saved to: {report_file}")
    
    # Print any issues encountered
    if analyzer.issues:
        print("\n⚠️  Issues encountered during analysis:")
        for issue_type, issues in analyzer.issues.items():
            print(f"  - {issue_type}: {len(issues)} issues")


if __name__ == "__main__":
    main()