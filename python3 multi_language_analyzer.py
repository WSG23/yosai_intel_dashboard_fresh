#!/usr/bin/env python3
"""
Multi-Language Code Analyzer for Yosai Intel Dashboard
Analyzes Python, Go, JavaScript, TypeScript, and other languages
"""

import ast
import json
import os
import re
import subprocess
import time
from collections import Counter, defaultdict
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple


class MultiLanguageAnalyzer:
    """Comprehensive analyzer for multi-language projects"""
    
    def __init__(self, project_path: str):
        self.project_path = Path(project_path)
        self.issues = defaultdict(list)
        self.exclude_dirs = {
            '.git', 'node_modules', '__pycache__', '.pytest_cache', 
            'venv', 'env', '.venv', 'dist', 'build', '.next',
            '.idea', '.vscode', 'coverage', 'htmlcov', 'vendor'
        }
        self.results = {}
        
    def analyze_project(self) -> Dict:
        """Run comprehensive multi-language analysis"""
        start_time = time.time()
        
        print(f"\n🔍 Analyzing multi-language project: {self.project_path}")
        print(f"   Excluding: {', '.join(sorted(self.exclude_dirs))}\n")
        
        # Detect project structure and languages
        project_info = self._analyze_project_structure()
        
        results = {
            'project_info': {
                'path': str(self.project_path),
                'languages': project_info['languages'],
                'primary_language': project_info['primary_language'],
                'is_monorepo': project_info['is_monorepo'],
                'analysis_time': 0
            },
            'summary': {},
            'python_analysis': {},
            'go_analysis': {},
            'javascript_analysis': {},
            'typescript_analysis': {},
            'security_scan': {},
            'dependency_analysis': {},
            'architecture_analysis': {},
            'migration_readiness': {}
        }
        
        # Run language-specific analyzers
        if project_info['languages'].get('Python', 0) > 0:
            print("🐍 Analyzing Python code...")
            results['python_analysis'] = self._analyze_python()
            
        if project_info['languages'].get('Go', 0) > 0:
            print("🐹 Analyzing Go code...")
            results['go_analysis'] = self._analyze_go()
            
        if project_info['languages'].get('JavaScript', 0) > 0:
            print("📜 Analyzing JavaScript code...")
            results['javascript_analysis'] = self._analyze_javascript()
            
        if project_info['languages'].get('TypeScript', 0) > 0:
            print("📘 Analyzing TypeScript code...")
            results['typescript_analysis'] = self._analyze_typescript()
        
        # Cross-language analysis
        print("🔒 Running security scan across all languages...")
        results['security_scan'] = self._cross_language_security_scan()
        
        print("📦 Analyzing dependencies...")
        results['dependency_analysis'] = self._analyze_dependencies()
        
        print("🏗️ Analyzing architecture...")
        results['architecture_analysis'] = self._analyze_architecture()
        
        print("🚀 Assessing migration readiness...")
        results['migration_readiness'] = self._assess_migration_readiness()
        
        # Generate summary
        results['summary'] = self._generate_summary(results)
        
        # Add timing
        results['project_info']['analysis_time'] = round(time.time() - start_time, 2)
        
        return results
    
    def _analyze_project_structure(self) -> Dict:
        """Detect languages and project structure"""
        file_counts = Counter()
        language_files = defaultdict(list)
        service_directories = []
        
        # Language mappings
        ext_to_language = {
            '.py': 'Python',
            '.go': 'Go',
            '.js': 'JavaScript',
            '.jsx': 'JavaScript',
            '.ts': 'TypeScript',
            '.tsx': 'TypeScript',
            '.java': 'Java',
            '.rs': 'Rust',
            '.cpp': 'C++',
            '.c': 'C',
            '.cs': 'C#',
            '.rb': 'Ruby',
            '.php': 'PHP',
            '.swift': 'Swift',
            '.kt': 'Kotlin',
            '.scala': 'Scala',
            '.r': 'R',
            '.m': 'Objective-C',
            '.dart': 'Dart',
            '.lua': 'Lua',
            '.pl': 'Perl',
            '.sh': 'Shell',
            '.yaml': 'YAML',
            '.yml': 'YAML',
            '.json': 'JSON',
            '.xml': 'XML',
            '.sql': 'SQL',
            '.proto': 'Protocol Buffers'
        }
        
        for file_path in self.project_path.rglob('*'):
            if file_path.is_file():
                if any(excluded in file_path.parts for excluded in self.exclude_dirs):
                    continue
                
                ext = file_path.suffix.lower()
                if ext in ext_to_language:
                    lang = ext_to_language[ext]
                    file_counts[lang] += 1
                    if lang in ['Python', 'Go', 'JavaScript', 'TypeScript']:
                        rel_path = file_path.relative_to(self.project_path)
                        language_files[lang].append(rel_path)
                
                # Detect service directories
                if file_path.name in ['go.mod', 'package.json', 'requirements.txt', 'pom.xml']:
                    service_dir = file_path.parent.relative_to(self.project_path)
                    if service_dir not in service_directories:
                        service_directories.append(str(service_dir))
        
        # Determine primary language
        primary_language = max(file_counts.items(), key=lambda x: x[1])[0] if file_counts else 'Unknown'
        
        # Check if it's a monorepo
        is_monorepo = (
            len([d for d in service_directories if '/' in d]) > 3 or
            (file_counts.get('Go', 0) > 10 and file_counts.get('Python', 0) > 10) or
            (file_counts.get('JavaScript', 0) + file_counts.get('TypeScript', 0) > 100 and 
             (file_counts.get('Python', 0) > 10 or file_counts.get('Go', 0) > 10))
        )
        
        return {
            'languages': dict(file_counts),
            'primary_language': primary_language,
            'language_files': dict(language_files),
            'service_directories': service_directories,
            'is_monorepo': is_monorepo,
            'total_source_files': sum(file_counts.values())
        }
    
    def _analyze_python(self) -> Dict:
        """Python-specific analysis"""
        python_files = list(self.project_path.rglob('*.py'))
        python_files = [f for f in python_files 
                        if not any(excluded in f.parts for excluded in self.exclude_dirs)]
        
        results = {
            'total_files': len(python_files),
            'code_quality': self._analyze_python_quality(python_files),
            'dependencies': self._analyze_python_dependencies(),
            'frameworks': self._detect_python_frameworks(python_files),
            'async_usage': self._analyze_python_async(python_files),
            'type_hints': self._analyze_python_type_hints(python_files)
        }
        
        return results
    
    def _analyze_go(self) -> Dict:
        """Go-specific analysis"""
        go_files = list(self.project_path.rglob('*.go'))
        go_files = [f for f in go_files 
                    if not any(excluded in f.parts for excluded in self.exclude_dirs)]
        
        results = {
            'total_files': len(go_files),
            'modules': self._analyze_go_modules(),
            'code_quality': self._analyze_go_quality(go_files),
            'concurrency': self._analyze_go_concurrency(go_files),
            'error_handling': self._analyze_go_error_handling(go_files),
            'test_coverage': self._estimate_go_test_coverage(go_files)
        }
        
        return results
    
    def _analyze_javascript(self) -> Dict:
        """JavaScript-specific analysis"""
        js_files = []
        for ext in ['*.js', '*.jsx']:
            js_files.extend(self.project_path.rglob(ext))
        js_files = [f for f in js_files 
                    if not any(excluded in f.parts for excluded in self.exclude_dirs)]
        
        results = {
            'total_files': len(js_files),
            'frameworks': self._detect_js_frameworks(),
            'code_quality': self._analyze_js_quality(js_files),
            'modern_syntax': self._analyze_js_modern_syntax(js_files),
            'react_patterns': self._analyze_react_patterns(js_files) if self._has_react() else {}
        }
        
        return results
    
    def _analyze_typescript(self) -> Dict:
        """TypeScript-specific analysis"""
        ts_files = []
        for ext in ['*.ts', '*.tsx']:
            ts_files.extend(self.project_path.rglob(ext))
        ts_files = [f for f in ts_files 
                    if not any(excluded in f.parts for excluded in self.exclude_dirs)]
        
        results = {
            'total_files': len(ts_files),
            'strict_mode': self._check_ts_strict_mode(),
            'type_safety': self._analyze_ts_type_safety(ts_files),
            'interfaces': self._analyze_ts_interfaces(ts_files),
            'react_patterns': self._analyze_react_patterns(ts_files) if self._has_react() else {}
        }
        
        return results
    
    def _analyze_python_quality(self, files: List[Path]) -> Dict:
        """Analyze Python code quality"""
        issues = defaultdict(list)
        metrics = {
            'total_lines': 0,
            'function_count': 0,
            'class_count': 0,
            'avg_function_length': 0
        }
        
        function_lengths = []
        
        for file_path in files:
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                    lines = content.splitlines()
                    metrics['total_lines'] += len(lines)
                    
                    tree = ast.parse(content)
                    
                    for node in ast.walk(tree):
                        if isinstance(node, ast.FunctionDef):
                            metrics['function_count'] += 1
                            if hasattr(node, 'end_lineno'):
                                length = node.end_lineno - node.lineno
                                function_lengths.append(length)
                                if length > 50:
                                    issues['long_functions'].append({
                                        'file': str(file_path.relative_to(self.project_path)),
                                        'function': node.name,
                                        'length': length
                                    })
                        elif isinstance(node, ast.ClassDef):
                            metrics['class_count'] += 1
                            
            except Exception as e:
                self.issues['python_parse_errors'].append(f"{file_path}: {e}")
        
        if function_lengths:
            metrics['avg_function_length'] = sum(function_lengths) / len(function_lengths)
        
        return {
            'metrics': metrics,
            'issues': dict(issues)
        }
    
    def _analyze_go_modules(self) -> Dict:
        """Analyze Go modules"""
        go_mods = list(self.project_path.rglob('go.mod'))
        modules = []
        
        for mod_file in go_mods:
            try:
                with open(mod_file, 'r') as f:
                    content = f.read()
                    module_match = re.search(r'module\s+(\S+)', content)
                    go_version_match = re.search(r'go\s+(\d+\.\d+)', content)
                    
                    if module_match:
                        rel_path = mod_file.parent.relative_to(self.project_path)
                        modules.append({
                            'path': str(rel_path),
                            'module': module_match.group(1),
                            'go_version': go_version_match.group(1) if go_version_match else 'unknown'
                        })
            except Exception as e:
                self.issues['go_mod_errors'].append(f"{mod_file}: {e}")
        
        return {
            'modules': modules,
            'total_modules': len(modules),
            'is_multi_module': len(modules) > 1
        }
    
    def _analyze_go_quality(self, files: List[Path]) -> Dict:
        """Analyze Go code quality"""
        issues = defaultdict(list)
        metrics = {
            'total_lines': 0,
            'function_count': 0,
            'interface_count': 0,
            'struct_count': 0
        }
        
        patterns = {
            'function': r'func\s+(?:\([^)]+\)\s+)?(\w+)',
            'interface': r'type\s+(\w+)\s+interface\s*{',
            'struct': r'type\s+(\w+)\s+struct\s*{',
            'error_check': r'if\s+err\s*!=\s*nil',
            'goroutine': r'go\s+\w+',
            'channel': r'chan\s+\w+|<-chan|chan<-'
        }
        
        for file_path in files:
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                    lines = content.splitlines()
                    metrics['total_lines'] += len(lines)
                    
                    # Count patterns
                    for name, pattern in patterns.items():
                        matches = re.findall(pattern, content)
                        if name == 'function':
                            metrics['function_count'] += len(matches)
                        elif name == 'interface':
                            metrics['interface_count'] += len(matches)
                        elif name == 'struct':
                            metrics['struct_count'] += len(matches)
                    
                    # Check for common issues
                    if not re.search(r'if\s+err\s*!=\s*nil', content) and 'error' in content:
                        issues['missing_error_handling'].append(
                            str(file_path.relative_to(self.project_path))
                        )
                        
            except Exception as e:
                self.issues['go_parse_errors'].append(f"{file_path}: {e}")
        
        return {
            'metrics': metrics,
            'issues': dict(issues)
        }
    
    def _analyze_js_quality(self, files: List[Path]) -> Dict:
        """Analyze JavaScript code quality"""
        issues = defaultdict(list)
        metrics = {
            'total_lines': 0,
            'function_count': 0,
            'class_count': 0,
            'arrow_functions': 0,
            'async_functions': 0
        }
        
        patterns = {
            'function': r'function\s+\w+',
            'arrow_function': r'=>',
            'class': r'class\s+\w+',
            'async_function': r'async\s+(?:function|\()',
            'console_log': r'console\.\w+',
            'var_usage': r'\bvar\s+\w+'
        }
        
        for file_path in files[:100]:  # Sample first 100 files for performance
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                    lines = content.splitlines()
                    metrics['total_lines'] += len(lines)
                    
                    # Count patterns
                    metrics['function_count'] += len(re.findall(patterns['function'], content))
                    metrics['arrow_functions'] += len(re.findall(patterns['arrow_function'], content))
                    metrics['class_count'] += len(re.findall(patterns['class'], content))
                    metrics['async_functions'] += len(re.findall(patterns['async_function'], content))
                    
                    # Check for issues
                    console_matches = re.findall(patterns['console_log'], content)
                    if console_matches:
                        issues['console_statements'].append({
                            'file': str(file_path.relative_to(self.project_path)),
                            'count': len(console_matches)
                        })
                    
                    var_matches = re.findall(patterns['var_usage'], content)
                    if var_matches:
                        issues['var_usage'].append({
                            'file': str(file_path.relative_to(self.project_path)),
                            'count': len(var_matches)
                        })
                        
            except Exception as e:
                self.issues['js_parse_errors'].append(f"{file_path}: {e}")
        
        return {
            'metrics': metrics,
            'issues': dict(issues),
            'sampled_files': min(100, len(files))
        }
    
    def _cross_language_security_scan(self) -> Dict:
        """Security scan across all languages"""
        vulnerabilities = defaultdict(list)
        
        # Common security patterns
        security_patterns = {
            'hardcoded_secret': [
                r'(?:password|passwd|pwd|secret|api_key|apikey|token)\s*[:=]\s*["\'][^"\']{8,}["\']',
                r'(?:AWS|aws)_?(?:SECRET|secret)_?(?:ACCESS|access)_?(?:KEY|key)',
                r'(?:PRIVATE|private)_?(?:KEY|key)',
            ],
            'sql_injection': [
                r'(?:SELECT|INSERT|UPDATE|DELETE|DROP).+\+\s*[\'"]',
                r'(?:execute|query)\([\'"].*%s',
                r'string\.Format.*(?:SELECT|INSERT|UPDATE|DELETE)',
            ],
            'command_injection': [
                r'exec\(|eval\(|system\(',
                r'subprocess\.(?:call|run|Popen).*shell\s*=\s*True',
                r'os\.system\(',
            ],
            'weak_crypto': [
                r'md5|MD5|sha1|SHA1',
                r'DES|3DES|RC4',
            ],
            'insecure_random': [
                r'math\.random\(\)|random\.random\(\)',
                r'rand\(\)|rand\.Int\(\)',
            ],
            'cors_wildcard': [
                r'Access-Control-Allow-Origin.*\*',
                r'AllowOrigins:\s*\[\s*["\']?\*',
            ]
        }
        
        # Scan all source files
        for ext in ['.py', '.go', '.js', '.jsx', '.ts', '.tsx', '.java', '.cs']:
            for file_path in self.project_path.rglob(f'*{ext}'):
                if any(excluded in file_path.parts for excluded in self.exclude_dirs):
                    continue
                
                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        content = f.read()
                        
                    for vuln_type, patterns in security_patterns.items():
                        for pattern in patterns:
                            matches = re.finditer(pattern, content, re.IGNORECASE)
                            for match in matches:
                                line_no = content[:match.start()].count('\n') + 1
                                vulnerabilities[vuln_type].append({
                                    'file': str(file_path.relative_to(self.project_path)),
                                    'line': line_no,
                                    'language': self._get_language_from_ext(ext),
                                    'match': match.group()[:50] + '...' if len(match.group()) > 50 else match.group()
                                })
                except Exception as e:
                    self.issues['security_scan_errors'].append(f"{file_path}: {e}")
        
        # Summary
        total_issues = sum(len(v) for v in vulnerabilities.values())
        
        return {
            'vulnerabilities': dict(vulnerabilities),
            'total_issues': total_issues,
            'severity_levels': {
                'critical': len(vulnerabilities.get('sql_injection', [])) + 
                           len(vulnerabilities.get('command_injection', [])),
                'high': len(vulnerabilities.get('hardcoded_secret', [])) + 
                        len(vulnerabilities.get('weak_crypto', [])),
                'medium': len(vulnerabilities.get('insecure_random', [])) + 
                          len(vulnerabilities.get('cors_wildcard', []))
            }
        }
    
    def _analyze_dependencies(self) -> Dict:
        """Analyze project dependencies across languages"""
        dependencies = {}
        
        # Python dependencies
        req_files = ['requirements.txt', 'Pipfile', 'pyproject.toml', 'setup.py']
        for req_file in req_files:
            req_path = self.project_path / req_file
            if req_path.exists():
                try:
                    with open(req_path, 'r') as f:
                        content = f.read()
                    dependencies['python'] = {
                        'file': req_file,
                        'count': len([l for l in content.splitlines() if l.strip() and not l.startswith('#')])
                    }
                    break
                except:
                    pass
        
        # JavaScript/TypeScript dependencies
        package_json = self.project_path / 'package.json'
        if package_json.exists():
            try:
                with open(package_json, 'r') as f:
                    pkg = json.load(f)
                dependencies['javascript'] = {
                    'dependencies': len(pkg.get('dependencies', {})),
                    'devDependencies': len(pkg.get('devDependencies', {})),
                    'total': len(pkg.get('dependencies', {})) + len(pkg.get('devDependencies', {}))
                }
            except:
                pass
        
        # Go dependencies
        go_mod = self.project_path / 'go.mod'
        if go_mod.exists():
            try:
                with open(go_mod, 'r') as f:
                    content = f.read()
                require_matches = re.findall(r'require\s*\(([^)]+)\)', content, re.DOTALL)
                if require_matches:
                    deps = [l.strip() for l in require_matches[0].splitlines() if l.strip()]
                    dependencies['go'] = {
                        'count': len(deps)
                    }
            except:
                pass
        
        return dependencies
    
    def _analyze_architecture(self) -> Dict:
        """Analyze project architecture"""
        architecture = {
            'patterns': [],
            'services': [],
            'api_style': None,
            'frontend_framework': None,
            'backend_framework': None,
            'database_detected': []
        }
        
        # Detect microservices
        service_indicators = ['service', 'api', 'gateway', 'worker', 'handler']
        for path in self.project_path.iterdir():
            if path.is_dir() and any(ind in path.name.lower() for ind in service_indicators):
                architecture['services'].append(path.name)
        
        # Detect API style
        if any(self.project_path.rglob('**/graphql/**')):
            architecture['api_style'] = 'GraphQL'
        elif any(self.project_path.rglob('**/*_pb2.py')) or any(self.project_path.rglob('*.proto')):
            architecture['api_style'] = 'gRPC'
        else:
            architecture['api_style'] = 'REST'
        
        # Detect frameworks
        if (self.project_path / 'package.json').exists():
            try:
                with open(self.project_path / 'package.json', 'r') as f:
                    pkg = json.load(f)
                    deps = pkg.get('dependencies', {})
                    if 'react' in deps:
                        architecture['frontend_framework'] = 'React'
                    elif 'vue' in deps:
                        architecture['frontend_framework'] = 'Vue'
                    elif '@angular/core' in deps:
                        architecture['frontend_framework'] = 'Angular'
            except:
                pass
        
        # Backend framework detection
        if any(self.project_path.rglob('**/flask/**')) or any(self.project_path.rglob('**/app.py')):
            architecture['backend_framework'] = 'Flask'
        elif any(self.project_path.rglob('**/django/**')) or (self.project_path / 'manage.py').exists():
            architecture['backend_framework'] = 'Django'
        elif any(self.project_path.rglob('**/fastapi/**')):
            architecture['backend_framework'] = 'FastAPI'
        elif any(self.project_path.rglob('**/gin/**')):
            architecture['backend_framework'] = 'Gin (Go)'
        
        # Database detection
        db_patterns = {
            'PostgreSQL': ['psycopg', 'postgresql', 'postgres'],
            'MySQL': ['mysqlclient', 'pymysql', 'mysql'],
            'MongoDB': ['pymongo', 'mongodb'],
            'Redis': ['redis', 'redis-py'],
            'SQLite': ['sqlite3', 'sqlite'],
            'Elasticsearch': ['elasticsearch', 'elastic']
        }
        
        all_files_sample = list(self.project_path.rglob('*'))[:1000]
        for file_path in all_files_sample:
            if file_path.is_file():
                try:
                    content = file_path.read_text()
                    for db, patterns in db_patterns.items():
                        if any(pattern in content.lower() for pattern in patterns):
                            if db not in architecture['database_detected']:
                                architecture['database_detected'].append(db)
                except:
                    continue
        
        return architecture
    
    def _assess_migration_readiness(self) -> Dict:
        """Assess readiness for microservices migration"""
        readiness = {
            'score': 0,
            'strengths': [],
            'weaknesses': [],
            'recommendations': []
        }
        
        # Check for existing microservices patterns
        if len(self._find_services()) > 3:
            readiness['strengths'].append("Already has service-oriented structure")
            readiness['score'] += 20
        else:
            readiness['weaknesses'].append("Monolithic structure needs decomposition")
            readiness['recommendations'].append("Identify bounded contexts for service extraction")
        
        # Check for API gateway
        if any(self.project_path.rglob('**/gateway/**')):
            readiness['strengths'].append("API Gateway pattern implemented")
            readiness['score'] += 15
        else:
            readiness['recommendations'].append("Implement API Gateway for service routing")
        
        # Check for containerization
        if (self.project_path / 'Dockerfile').exists() or any(self.project_path.rglob('**/Dockerfile')):
            readiness['strengths'].append("Containerization in place")
            readiness['score'] += 15
        else:
            readiness['weaknesses'].append("No containerization found")
            readiness['recommendations'].append("Add Dockerfiles for each service")
        
        # Check for orchestration
        if any(self.project_path.rglob('**/*.yaml')) and (
            any(self.project_path.rglob('**/k8s/**')) or 
            any(self.project_path.rglob('**/kubernetes/**'))
        ):
            readiness['strengths'].append("Kubernetes configurations found")
            readiness['score'] += 20
        else:
            readiness['recommendations'].append("Add Kubernetes manifests for orchestration")
        
        # Check for service mesh
        if any(self.project_path.rglob('**/istio/**')) or any(self.project_path.rglob('**/linkerd/**')):
            readiness['strengths'].append("Service mesh configuration detected")
            readiness['score'] += 10
        
        # Check for monitoring
        if any(self.project_path.rglob('**/prometheus/**')) or any(self.project_path.rglob('**/grafana/**')):
            readiness['strengths'].append("Monitoring infrastructure present")
            readiness['score'] += 10
        else:
            readiness['recommendations'].append("Implement distributed monitoring and tracing")
        
        # Check for CI/CD
        if (self.project_path / '.github' / 'workflows').exists() or \
           (self.project_path / '.gitlab-ci.yml').exists() or \
           (self.project_path / 'Jenkinsfile').exists():
            readiness['strengths'].append("CI/CD pipeline configured")
            readiness['score'] += 10
        else:
            readiness['recommendations'].append("Set up CI/CD pipelines for automated deployment")
        
        # Final assessment
        if readiness['score'] >= 70:
            readiness['assessment'] = "Ready for microservices migration"
        elif readiness['score'] >= 40:
            readiness['assessment'] = "Partially ready, needs some preparation"
        else:
            readiness['assessment'] = "Significant preparation needed"
        
        return readiness
    
    def _find_services(self) -> List[str]:
        """Find potential service directories"""
        services = []
        service_indicators = ['service', 'api', 'gateway', 'worker', 'microservice']
        
        for path in self.project_path.iterdir():
            if path.is_dir():
                if any(ind in path.name.lower() for ind in service_indicators):
                    services.append(path.name)
                elif (path / 'go.mod').exists() or (path / 'package.json').exists():
                    services.append(path.name)
        
        return services
    
    def _generate_summary(self, results: Dict) -> Dict:
        """Generate executive summary"""
        summary = {
            'total_files': results['project_info'].get('total_source_files', 0),
            'languages': results['project_info']['languages'],
            'primary_language': results['project_info']['primary_language'],
            'critical_issues': 0,
            'migration_score': results.get('migration_readiness', {}).get('score', 0),
            'key_findings': [],
            'immediate_actions': []
        }
        
        # Count critical issues
        if 'security_scan' in results:
            summary['critical_issues'] += results['security_scan'].get('severity_levels', {}).get('critical', 0)
        
        # Key findings
        if results['project_info']['is_monorepo']:
            summary['key_findings'].append("Monorepo structure detected - good for microservices migration")
        
        if results.get('python_analysis', {}).get('total_files', 0) > 100:
            summary['key_findings'].append(f"Large Python codebase with {results['python_analysis']['total_files']} files")
        
        if results.get('go_analysis', {}).get('modules', {}).get('is_multi_module'):
            summary['key_findings'].append("Multiple Go modules detected - modular architecture")
        
        # Immediate actions
        if summary['critical_issues'] > 0:
            summary['immediate_actions'].append(f"Fix {summary['critical_issues']} critical security vulnerabilities")
        
        if results.get('migration_readiness', {}).get('score', 0) < 40:
            summary['immediate_actions'].append("Prepare infrastructure for microservices migration")
        
        return summary
    
    # Helper methods
    def _get_language_from_ext(self, ext: str) -> str:
        """Get language name from file extension"""
        ext_map = {
            '.py': 'Python',
            '.go': 'Go',
            '.js': 'JavaScript',
            '.jsx': 'JavaScript',
            '.ts': 'TypeScript',
            '.tsx': 'TypeScript',
            '.java': 'Java',
            '.cs': 'C#'
        }
        return ext_map.get(ext, 'Unknown')
    
    def _detect_python_frameworks(self, files: List[Path]) -> List[str]:
        """Detect Python frameworks in use"""
        frameworks = []
        
        # Check imports in sample of files
        for file_path in files[:50]:
            try:
                with open(file_path, 'r') as f:
                    content = f.read()
                    if 'from flask' in content or 'import flask' in content:
                        frameworks.append('Flask')
                    if 'from django' in content or 'import django' in content:
                        frameworks.append('Django')
                    if 'from fastapi' in content or 'import fastapi' in content:
                        frameworks.append('FastAPI')
                    if 'import asyncio' in content:
                        frameworks.append('AsyncIO')
            except:
                continue
        
        return list(set(frameworks))
    
    def _analyze_python_dependencies(self) -> Dict:
        """Analyze Python dependencies"""
        deps = {'count': 0, 'file': None}
        
        for dep_file in ['requirements.txt', 'Pipfile', 'pyproject.toml']:
            path = self.project_path / dep_file
            if path.exists():
                deps['file'] = dep_file
                try:
                    content = path.read_text()
                    if dep_file == 'requirements.txt':
                        deps['count'] = len([l for l in content.splitlines() 
                                           if l.strip() and not l.startswith('#')])
                    break
                except:
                    pass
        
        return deps
    
    def _analyze_python_async(self, files: List[Path]) -> Dict:
        """Analyze async/await usage in Python"""
        async_stats = {
            'files_with_async': 0,
            'async_functions': 0,
            'await_statements': 0
        }
        
        for file_path in files[:100]:  # Sample
            try:
                with open(file_path, 'r') as f:
                    content = f.read()
                    if 'async def' in content or 'async with' in content:
                        async_stats['files_with_async'] += 1
                        async_stats['async_functions'] += len(re.findall(r'async\s+def', content))
                        async_stats['await_statements'] += len(re.findall(r'await\s+', content))
            except:
                continue
        
        return async_stats
    
    def _analyze_python_type_hints(self, files: List[Path]) -> Dict:
        """Analyze type hint usage in Python"""
        type_stats = {
            'files_with_hints': 0,
            'functions_with_hints': 0,
            'total_functions': 0
        }
        
        for file_path in files[:100]:  # Sample
            try:
                with open(file_path, 'r') as f:
                    content = f.read()
                    if '->' in content or ': ' in content:
                        type_stats['files_with_hints'] += 1
                    
                    # Count functions with return type hints
                    type_stats['functions_with_hints'] += len(re.findall(r'def\s+\w+\([^)]*\)\s*->', content))
                    type_stats['total_functions'] += len(re.findall(r'def\s+\w+\(', content))
            except:
                continue
        
        if type_stats['total_functions'] > 0:
            type_stats['percentage'] = round(
                type_stats['functions_with_hints'] / type_stats['total_functions'] * 100, 1
            )
        
        return type_stats
    
    def _analyze_go_concurrency(self, files: List[Path]) -> Dict:
        """Analyze Go concurrency patterns"""
        concurrency = {
            'goroutines': 0,
            'channels': 0,
            'mutexes': 0,
            'waitgroups': 0
        }
        
        for file_path in files[:100]:  # Sample
            try:
                with open(file_path, 'r') as f:
                    content = f.read()
                    concurrency['goroutines'] += len(re.findall(r'go\s+\w+', content))
                    concurrency['channels'] += len(re.findall(r'chan\s+', content))
                    concurrency['mutexes'] += len(re.findall(r'sync\.Mutex', content))
                    concurrency['waitgroups'] += len(re.findall(r'sync\.WaitGroup', content))
            except:
                continue
        
        return concurrency
    
    def _analyze_go_error_handling(self, files: List[Path]) -> Dict:
        """Analyze Go error handling patterns"""
        error_handling = {
            'error_checks': 0,
            'panic_usage': 0,
            'recover_usage': 0
        }
        
        for file_path in files[:100]:  # Sample
            try:
                with open(file_path, 'r') as f:
                    content = f.read()
                    error_handling['error_checks'] += len(re.findall(r'if\s+err\s*!=\s*nil', content))
                    error_handling['panic_usage'] += len(re.findall(r'panic\(', content))
                    error_handling['recover_usage'] += len(re.findall(r'recover\(\)', content))
            except:
                continue
        
        return error_handling
    
    def _estimate_go_test_coverage(self, files: List[Path]) -> Dict:
        """Estimate Go test coverage"""
        test_files = [f for f in files if '_test.go' in f.name]
        source_files = [f for f in files if '_test.go' not in f.name]
        
        return {
            'test_files': len(test_files),
            'source_files': len(source_files),
            'test_ratio': round(len(test_files) / len(source_files) * 100, 1) if source_files else 0
        }
    
    def _detect_js_frameworks(self) -> List[str]:
        """Detect JavaScript frameworks"""
        frameworks = []
        
        package_json = self.project_path / 'package.json'
        if package_json.exists():
            try:
                with open(package_json, 'r') as f:
                    pkg = json.load(f)
                    deps = {**pkg.get('dependencies', {}), **pkg.get('devDependencies', {})}
                    
                    if 'react' in deps:
                        frameworks.append('React')
                    if 'vue' in deps:
                        frameworks.append('Vue')
                    if '@angular/core' in deps:
                        frameworks.append('Angular')
                    if 'express' in deps:
                        frameworks.append('Express')
                    if 'next' in deps:
                        frameworks.append('Next.js')
                    if 'gatsby' in deps:
                        frameworks.append('Gatsby')
            except:
                pass
        
        return frameworks
    
    def _analyze_js_modern_syntax(self, files: List[Path]) -> Dict:
        """Analyze modern JavaScript syntax usage"""
        modern_syntax = {
            'es6_modules': 0,
            'arrow_functions': 0,
            'template_literals': 0,
            'destructuring': 0,
            'spread_operator': 0
        }
        
        for file_path in files[:100]:  # Sample
            try:
                with open(file_path, 'r') as f:
                    content = f.read()
                    modern_syntax['es6_modules'] += len(re.findall(r'import\s+.*from|export\s+', content))
                    modern_syntax['arrow_functions'] += len(re.findall(r'=>', content))
                    modern_syntax['template_literals'] += len(re.findall(r'`[^`]*\$\{[^}]+\}[^`]*`', content))
                    modern_syntax['destructuring'] += len(re.findall(r'const\s*{[^}]+}', content))
                    modern_syntax['spread_operator'] += len(re.findall(r'\.\.\.', content))
            except:
                continue
        
        return modern_syntax
    
    def _analyze_react_patterns(self, files: List[Path]) -> Dict:
        """Analyze React patterns"""
        react_patterns = {
            'functional_components': 0,
            'class_components': 0,
            'hooks_usage': 0,
            'jsx_files': 0
        }
        
        for file_path in files[:100]:  # Sample
            if file_path.suffix in ['.jsx', '.tsx']:
                react_patterns['jsx_files'] += 1
            
            try:
                with open(file_path, 'r') as f:
                    content = f.read()
                    react_patterns['functional_components'] += len(re.findall(r'(?:function|const)\s+\w+\s*\([^)]*\)\s*{[^}]*return\s*\(', content))
                    react_patterns['class_components'] += len(re.findall(r'class\s+\w+\s+extends\s+(?:React\.)?Component', content))
                    react_patterns['hooks_usage'] += len(re.findall(r'use(?:State|Effect|Context|Reducer|Callback|Memo)', content))
            except:
                continue
        
        return react_patterns
    
    def _has_react(self) -> bool:
        """Check if project uses React"""
        package_json = self.project_path / 'package.json'
        if package_json.exists():
            try:
                with open(package_json, 'r') as f:
                    pkg = json.load(f)
                    deps = {**pkg.get('dependencies', {}), **pkg.get('devDependencies', {})}
                    return 'react' in deps
            except:
                pass
        return False
    
    def _check_ts_strict_mode(self) -> bool:
        """Check if TypeScript strict mode is enabled"""
        tsconfig = self.project_path / 'tsconfig.json'
        if tsconfig.exists():
            try:
                with open(tsconfig, 'r') as f:
                    config = json.load(f)
                    compiler_options = config.get('compilerOptions', {})
                    return compiler_options.get('strict', False)
            except:
                pass
        return False
    
    def _analyze_ts_type_safety(self, files: List[Path]) -> Dict:
        """Analyze TypeScript type safety"""
        type_safety = {
            'any_usage': 0,
            'unknown_usage': 0,
            'type_assertions': 0,
            'non_null_assertions': 0
        }
        
        for file_path in files[:100]:  # Sample
            try:
                with open(file_path, 'r') as f:
                    content = f.read()
                    type_safety['any_usage'] += len(re.findall(r':\s*any\b', content))
                    type_safety['unknown_usage'] += len(re.findall(r':\s*unknown\b', content))
                    type_safety['type_assertions'] += len(re.findall(r'as\s+\w+', content))
                    type_safety['non_null_assertions'] += len(re.findall(r'\w+!', content))
            except:
                continue
        
        return type_safety
    
    def _analyze_ts_interfaces(self, files: List[Path]) -> Dict:
        """Analyze TypeScript interfaces and types"""
        ts_types = {
            'interfaces': 0,
            'type_aliases': 0,
            'enums': 0,
            'generics': 0
        }
        
        for file_path in files[:100]:  # Sample
            try:
                with open(file_path, 'r') as f:
                    content = f.read()
                    ts_types['interfaces'] += len(re.findall(r'interface\s+\w+', content))
                    ts_types['type_aliases'] += len(re.findall(r'type\s+\w+\s*=', content))
                    ts_types['enums'] += len(re.findall(r'enum\s+\w+', content))
                    ts_types['generics'] += len(re.findall(r'<[A-Z]\w*>', content))
            except:
                continue
        
        return ts_types
    
    def generate_report(self, results: Dict) -> str:
        """Generate comprehensive multi-language report"""
        report = []
        report.append("# Multi-Language Code Analysis Report\n")
        report.append(f"Project: {results['project_info']['path']}")
        report.append(f"Analysis completed in: {results['project_info']['analysis_time']}s\n")
        
        # Executive Summary
        summary = results.get('summary', {})
        report.append("## Executive Summary")
        report.append(f"- **Primary Language**: {summary.get('primary_language', 'Unknown')}")
        report.append(f"- **Total Source Files**: {summary.get('total_files', 0):,}")
        report.append(f"- **Critical Security Issues**: {summary.get('critical_issues', 0)}")
        report.append(f"- **Migration Readiness Score**: {summary.get('migration_score', 0)}/100")
        
        if summary.get('key_findings'):
            report.append("\n### Key Findings:")
            for finding in summary['key_findings']:
                report.append(f"- {finding}")
        
        if summary.get('immediate_actions'):
            report.append("\n### Immediate Actions Required:")
            for action in summary['immediate_actions']:
                report.append(f"- 🚨 {action}")
        
        # Language Distribution
        report.append("\n## Language Distribution")
        languages = results['project_info'].get('languages', {})
        for lang, count in sorted(languages.items(), key=lambda x: x[1], reverse=True)[:10]:
            percentage = (count / summary.get('total_files', 1)) * 100
            report.append(f"- **{lang}**: {count:,} files ({percentage:.1f}%)")
        
        # Python Analysis
        if results.get('python_analysis') and results['python_analysis'].get('total_files', 0) > 0:
            py = results['python_analysis']
            report.append("\n## Python Analysis")
            report.append(f"- **Total Files**: {py['total_files']}")
            report.append(f"- **Total Lines**: {py['code_quality']['metrics']['total_lines']:,}")
            report.append(f"- **Functions**: {py['code_quality']['metrics']['function_count']}")
            report.append(f"- **Classes**: {py['code_quality']['metrics']['class_count']}")
            report.append(f"- **Avg Function Length**: {py['code_quality']['metrics']['avg_function_length']:.1f} lines")
            
            if py.get('frameworks'):
                report.append(f"- **Frameworks**: {', '.join(py['frameworks'])}")
            
            if py.get('type_hints', {}).get('percentage'):
                report.append(f"- **Type Hint Coverage**: {py['type_hints']['percentage']}%")
        
        # Go Analysis
        if results.get('go_analysis') and results['go_analysis'].get('total_files', 0) > 0:
            go = results['go_analysis']
            report.append("\n## Go Analysis")
            report.append(f"- **Total Files**: {go['total_files']}")
            report.append(f"- **Modules**: {go['modules']['total_modules']}")
            report.append(f"- **Functions**: {go['code_quality']['metrics']['function_count']}")
            report.append(f"- **Interfaces**: {go['code_quality']['metrics']['interface_count']}")
            report.append(f"- **Structs**: {go['code_quality']['metrics']['struct_count']}")
            
            if go['modules']['modules']:
                report.append("\n### Go Modules:")
                for mod in go['modules']['modules'][:5]:
                    report.append(f"  - {mod['module']} (Go {mod['go_version']})")
        
        # JavaScript Analysis
        if results.get('javascript_analysis') and results['javascript_analysis'].get('total_files', 0) > 0:
            js = results['javascript_analysis']
            report.append("\n## JavaScript Analysis")
            report.append(f"- **Total Files**: {js['total_files']}")
            if js.get('frameworks'):
                report.append(f"- **Frameworks**: {', '.join(js['frameworks'])}")
            report.append(f"- **Modern Syntax Usage**: High" if js.get('modern_syntax', {}).get('arrow_functions', 0) > 100 else "- **Modern Syntax Usage**: Low")
        
        # TypeScript Analysis
        if results.get('typescript_analysis') and results['typescript_analysis'].get('total_files', 0) > 0:
            ts = results['typescript_analysis']
            report.append("\n## TypeScript Analysis")
            report.append(f"- **Total Files**: {ts['total_files']}")
            report.append(f"- **Strict Mode**: {'Enabled' if ts.get('strict_mode') else 'Disabled'}")
            report.append(f"- **Interfaces Defined**: {ts.get('interfaces', {}).get('interfaces', 0)}")
        
        # Security Analysis
        security = results.get('security_scan', {})
        if security.get('total_issues', 0) > 0:
            report.append("\n## 🔒 Security Analysis")
            report.append(f"**Total Issues Found**: {security['total_issues']}")
            
            severity = security.get('severity_levels', {})
            report.append(f"- Critical: {severity.get('critical', 0)}")
            report.append(f"- High: {severity.get('high', 0)}")
            report.append(f"- Medium: {severity.get('medium', 0)}")
            
            if security.get('vulnerabilities'):
                report.append("\n### Top Security Concerns:")
                for vuln_type, issues in list(security['vulnerabilities'].items())[:5]:
                    report.append(f"- **{vuln_type.replace('_', ' ').title()}**: {len(issues)} occurrences")
        
        # Architecture Analysis
        arch = results.get('architecture_analysis', {})
        if arch:
            report.append("\n## Architecture Analysis")
            report.append(f"- **API Style**: {arch.get('api_style', 'Unknown')}")
            report.append(f"- **Frontend**: {arch.get('frontend_framework', 'Not detected')}")
            report.append(f"- **Backend**: {arch.get('backend_framework', 'Not detected')}")
            if arch.get('database_detected'):
                report.append(f"- **Databases**: {', '.join(arch['database_detected'])}")
            if arch.get('services'):
                report.append(f"- **Services Detected**: {len(arch['services'])}")
        
        # Migration Readiness
        migration = results.get('migration_readiness', {})
        if migration:
            report.append("\n## Microservices Migration Readiness")
            report.append(f"**Overall Score**: {migration.get('score', 0)}/100")
            report.append(f"**Assessment**: {migration.get('assessment', 'Unknown')}")
            
            if migration.get('strengths'):
                report.append("\n### Strengths:")
                for strength in migration['strengths']:
                    report.append(f"- ✅ {strength}")
            
            if migration.get('weaknesses'):
                report.append("\n### Weaknesses:")
                for weakness in migration['weaknesses']:
                    report.append(f"- ❌ {weakness}")
            
            if migration.get('recommendations'):
                report.append("\n### Recommendations:")
                for rec in migration['recommendations']:
                    report.append(f"- 💡 {rec}")
        
        # Next Steps
        report.append("\n## Next Steps")
        report.append("1. Address critical security vulnerabilities immediately")
        report.append("2. Review and implement migration recommendations")
        report.append("3. Establish code quality standards across all languages")
        report.append("4. Set up comprehensive testing for all services")
        report.append("5. Implement monitoring and observability")
        
        return '\n'.join(report)


def main():
    """Run the multi-language analyzer"""
    import argparse
    import sys
    
    parser = argparse.ArgumentParser(description='Analyze multi-language projects')
    parser.add_argument('project_path', help='Path to the project directory')
    parser.add_argument('--output', '-o', default='multi_language_analysis', 
                       help='Output filename prefix (default: multi_language_analysis)')
    parser.add_argument('--languages', '-l', nargs='+', 
                       help='Specific languages to analyze (default: all)')
    
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
    analyzer = MultiLanguageAnalyzer(project_path)
    results = analyzer.analyze_project()
    
    # Save results
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
    print(f"📊 Detailed results: {json_file}")
    print(f"📄 Report: {report_file}")
    
    # Summary statistics
    summary = results.get('summary', {})
    print(f"\n📈 Quick Stats:")
    print(f"   Languages found: {len(results['project_info']['languages'])}")
    print(f"   Total files analyzed: {summary.get('total_files', 0):,}")
    print(f"   Critical issues: {summary.get('critical_issues', 0)}")
    print(f"   Migration readiness: {summary.get('migration_score', 0)}/100")


if __name__ == "__main__":
    main()