#!/usr/bin/env python3
"""
Simplified Multi-Language Analyzer - Robust Version
Focuses on essential analysis without complex dependencies
"""

import json
import os
import re
from collections import Counter, defaultdict
from datetime import datetime
from pathlib import Path


class SimpleMultiLanguageAnalyzer:
    def __init__(self, project_path: str):
        self.project_path = Path(project_path)
        self.exclude_dirs = {
            '.git', 'node_modules', '__pycache__', '.pytest_cache', 
            'venv', 'env', '.venv', 'dist', 'build', '.next',
            '.idea', '.vscode', 'coverage', 'htmlcov', 'vendor'
        }
        self.results = defaultdict(dict)
        
    def analyze(self):
        """Run the complete analysis"""
        print(f"\n🔍 Analyzing: {self.project_path.absolute()}")
        print("=" * 60)
        
        # Step 1: Scan files
        print("\n📁 Scanning project structure...")
        file_stats = self._scan_files()
        
        # Step 2: Security scan
        print("\n🔒 Running security scan...")
        security_issues = self._security_scan(file_stats['files_by_type'])
        
        # Step 3: Code quality
        print("\n📊 Analyzing code quality...")
        quality_issues = self._quality_scan(file_stats['files_by_type'])
        
        # Step 4: Architecture
        print("\n🏗️ Analyzing architecture...")
        architecture = self._analyze_architecture()
        
        # Compile results
        self.results = {
            'project_path': str(self.project_path),
            'scan_time': datetime.now().isoformat(),
            'file_statistics': file_stats,
            'security_scan': security_issues,
            'code_quality': quality_issues,
            'architecture': architecture,
            'summary': self._generate_summary(file_stats, security_issues, quality_issues, architecture)
        }
        
        return self.results
    
    def _scan_files(self):
        """Scan all files in the project"""
        stats = {
            'total_files': 0,
            'excluded_files': 0,
            'analyzed_files': 0,
            'files_by_language': Counter(),
            'files_by_type': defaultdict(list),
            'language_lines': Counter()
        }
        
        ext_to_lang = {
            '.py': 'Python', '.pyx': 'Python', '.pyw': 'Python',
            '.go': 'Go',
            '.js': 'JavaScript', '.jsx': 'JavaScript', '.mjs': 'JavaScript',
            '.ts': 'TypeScript', '.tsx': 'TypeScript',
            '.java': 'Java',
            '.cs': 'C#',
            '.rb': 'Ruby',
            '.php': 'PHP',
            '.rs': 'Rust',
            '.swift': 'Swift',
            '.kt': 'Kotlin', '.kts': 'Kotlin',
            '.scala': 'Scala',
            '.cpp': 'C++', '.cc': 'C++', '.cxx': 'C++',
            '.c': 'C', '.h': 'C',
            '.r': 'R',
            '.m': 'Objective-C',
            '.sh': 'Shell', '.bash': 'Shell',
            '.sql': 'SQL',
            '.yaml': 'YAML', '.yml': 'YAML',
            '.json': 'JSON',
            '.xml': 'XML',
            '.html': 'HTML', '.htm': 'HTML',
            '.css': 'CSS', '.scss': 'CSS', '.sass': 'CSS',
            '.proto': 'Protocol Buffers'
        }
        
        for file_path in self.project_path.rglob('*'):
            if file_path.is_file():
                stats['total_files'] += 1
                
                # Check exclusions
                if any(exc in file_path.parts for exc in self.exclude_dirs):
                    stats['excluded_files'] += 1
                    continue
                
                ext = file_path.suffix.lower()
                if ext in ext_to_lang:
                    lang = ext_to_lang[ext]
                    stats['files_by_language'][lang] += 1
                    stats['files_by_type'][lang].append(file_path)
                    stats['analyzed_files'] += 1
                    
                    # Count lines for main languages
                    if lang in ['Python', 'Go', 'JavaScript', 'TypeScript', 'Java']:
                        try:
                            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                                lines = len(f.readlines())
                                stats['language_lines'][lang] += lines
                        except:
                            pass
        
        return stats
    
    def _security_scan(self, files_by_type):
        """Scan for security issues"""
        issues = defaultdict(list)
        severity_count = Counter()
        
        patterns = {
            'hardcoded_secrets': {
                'pattern': r'(?i)(password|passwd|pwd|secret|api_key|apikey|token|private_key)\s*[:=]\s*["\'][^"\']{8,}["\']',
                'severity': 'HIGH',
                'languages': ['Python', 'JavaScript', 'TypeScript', 'Go', 'Java', 'Ruby', 'PHP']
            },
            'sql_injection': {
                'pattern': r'(?i)(select|insert|update|delete|drop)\s+.*\+\s*["\']|\.format\(.*(?:select|insert|update|delete)',
                'severity': 'CRITICAL',
                'languages': ['Python', 'JavaScript', 'TypeScript', 'Go', 'Java', 'Ruby', 'PHP']
            },
            'command_injection': {
                'pattern': r'(?:exec|eval|system|subprocess\.call|os\.system|child_process\.exec)\s*\(',
                'severity': 'CRITICAL',
                'languages': ['Python', 'JavaScript', 'TypeScript', 'Ruby', 'PHP']
            },
            'weak_crypto': {
                'pattern': r'(?i)(md5|sha1|des|rc4)\s*\(',
                'severity': 'MEDIUM',
                'languages': ['Python', 'JavaScript', 'TypeScript', 'Go', 'Java']
            },
            'debug_mode': {
                'pattern': r'(?i)debug\s*=\s*true|DEBUG\s*=\s*True',
                'severity': 'LOW',
                'languages': ['Python', 'JavaScript', 'TypeScript']
            }
        }
        
        files_scanned = 0
        for vuln_name, config in patterns.items():
            for lang in config['languages']:
                if lang not in files_by_type:
                    continue
                    
                # Sample files for performance
                files_to_scan = files_by_type[lang][:50]  # Scan up to 50 files per language
                
                for file_path in files_to_scan:
                    files_scanned += 1
                    try:
                        with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                            content = f.read()
                            
                        matches = re.finditer(config['pattern'], content)
                        for match in matches:
                            line_no = content[:match.start()].count('\n') + 1
                            issues[vuln_name].append({
                                'file': str(file_path.relative_to(self.project_path)),
                                'line': line_no,
                                'severity': config['severity'],
                                'language': lang,
                                'match': match.group()[:50]
                            })
                            severity_count[config['severity']] += 1
                    except Exception as e:
                        pass
        
        return {
            'issues': dict(issues),
            'severity_summary': dict(severity_count),
            'files_scanned': files_scanned,
            'total_issues': sum(len(v) for v in issues.values())
        }
    
    def _quality_scan(self, files_by_type):
        """Scan for code quality issues"""
        quality_metrics = {
            'languages': {},
            'total_issues': 0
        }
        
        # Python quality checks
        if 'Python' in files_by_type:
            py_metrics = self._analyze_python_quality(files_by_type['Python'][:50])
            quality_metrics['languages']['Python'] = py_metrics
            quality_metrics['total_issues'] += py_metrics.get('issues_found', 0)
        
        # Go quality checks
        if 'Go' in files_by_type:
            go_metrics = self._analyze_go_quality(files_by_type['Go'][:50])
            quality_metrics['languages']['Go'] = go_metrics
            quality_metrics['total_issues'] += go_metrics.get('issues_found', 0)
        
        # JavaScript/TypeScript quality checks
        for lang in ['JavaScript', 'TypeScript']:
            if lang in files_by_type:
                js_metrics = self._analyze_js_quality(files_by_type[lang][:50], lang)
                quality_metrics['languages'][lang] = js_metrics
                quality_metrics['total_issues'] += js_metrics.get('issues_found', 0)
        
        return quality_metrics
    
    def _read_file_content(self, file_path: Path) -> str:
        """Return the text content of ``file_path`` or an empty string."""
        try:
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                return f.read()
        except Exception:
            return ""

    def _python2_detected(self, content: str) -> bool:
        """Return ``True`` if Python 2 specific syntax is found."""
        return bool(re.search(r'print\s+["\']|xrange\(|raw_input\(', content))

    def _missing_docstring(self, content: str) -> bool:
        """Return ``True`` when a function lacks a docstring."""
        return 'def ' in content and '"""' not in content

    def _has_long_functions(self, content: str) -> bool:
        """Heuristically detect very long functions in ``content``."""
        functions = re.findall(r'def\s+\w+\(.*?\):', content)
        return len(functions) > 0 and len(content.splitlines()) / max(len(functions), 1) > 50

    def _analyze_python_quality(self, files):
        """Analyze Python code quality and return aggregated metrics."""
        metrics = {
            'files_analyzed': len(files),
            'issues_found': 0,
            'python2_code': 0,
            'missing_docstrings': 0,
            'long_functions': 0
        }

        for file_path in files:
            content = self._read_file_content(file_path)
            if not content:
                continue

            if self._python2_detected(content):
                metrics['python2_code'] += 1
                metrics['issues_found'] += 1

            if self._missing_docstring(content):
                metrics['missing_docstrings'] += 1
                metrics['issues_found'] += 1

            if self._has_long_functions(content):
                metrics['long_functions'] += 1
                metrics['issues_found'] += 1

        return metrics
    
    def _go_missing_error_handling(self, content: str) -> bool:
        """Return ``True`` when blank identifier error handling is detected."""
        return '_' in content and 'err' in content and bool(re.search(r'_,\s*err\s*:=', content))

    def _go_has_todo(self, content: str) -> bool:
        """Return ``True`` if TODO or FIXME comments are present."""
        return bool(re.search(r'//\s*TODO|//\s*FIXME', content, re.IGNORECASE))

    def _analyze_go_quality(self, files):
        """Analyze Go code quality and return aggregated metrics."""
        metrics = {
            'files_analyzed': len(files),
            'issues_found': 0,
            'missing_error_handling': 0,
            'todo_comments': 0
        }

        for file_path in files:
            content = self._read_file_content(file_path)
            if not content:
                continue

            if self._go_missing_error_handling(content):
                metrics['missing_error_handling'] += 1
                metrics['issues_found'] += 1

            if self._go_has_todo(content):
                metrics['todo_comments'] += 1

        return metrics
    
    def _has_console_log(self, content: str) -> bool:
        """Detect console logging statements."""
        return 'console.' in content

    def _uses_var(self, content: str) -> bool:
        """Return ``True`` if ``var`` declarations are used."""
        return bool(re.search(r'\bvar\s+\w+', content))

    def _missing_strict_mode(self, content: str) -> bool:
        """Check whether the ``'use strict'`` directive is absent."""
        return '"use strict"' not in content and "'use strict'" not in content

    def _analyze_js_quality(self, files, language):
        """Analyze JavaScript or TypeScript code quality and return metrics."""
        metrics = {
            'files_analyzed': len(files),
            'issues_found': 0,
            'console_logs': 0,
            'var_usage': 0,
            'no_strict': 0
        }

        for file_path in files:
            content = self._read_file_content(file_path)
            if not content:
                continue

            if self._has_console_log(content):
                metrics['console_logs'] += 1
                metrics['issues_found'] += 1

            if self._uses_var(content):
                metrics['var_usage'] += 1
                metrics['issues_found'] += 1

            if language == 'JavaScript' and self._missing_strict_mode(content):
                metrics['no_strict'] += 1

        return metrics
    
    def _analyze_architecture(self):
        """Analyze project architecture"""
        architecture = {
            'structure': 'unknown',
            'services': [],
            'frameworks': [],
            'databases': [],
            'api_style': 'unknown'
        }
        
        # Check for microservices
        service_dirs = []
        for path in self.project_path.iterdir():
            if path.is_dir() and not path.name.startswith('.'):
                # Check if it has its own package file
                if (path / 'package.json').exists() or \
                   (path / 'go.mod').exists() or \
                   (path / 'requirements.txt').exists() or \
                   (path / 'pom.xml').exists():
                    service_dirs.append(path.name)
        
        architecture['services'] = service_dirs
        
        if len(service_dirs) > 3:
            architecture['structure'] = 'microservices'
        elif len(service_dirs) > 0:
            architecture['structure'] = 'modular'
        else:
            architecture['structure'] = 'monolithic'
        
        # Detect frameworks
        if (self.project_path / 'package.json').exists():
            try:
                with open(self.project_path / 'package.json', 'r') as f:
                    pkg = json.load(f)
                    deps = {**pkg.get('dependencies', {}), **pkg.get('devDependencies', {})}
                    
                    if 'react' in deps:
                        architecture['frameworks'].append('React')
                    if 'express' in deps:
                        architecture['frameworks'].append('Express')
                    if '@angular/core' in deps:
                        architecture['frameworks'].append('Angular')
                    if 'vue' in deps:
                        architecture['frameworks'].append('Vue')
            except:
                pass
        
        # Check for Python frameworks
        req_files = list(self.project_path.glob('**/requirements*.txt'))
        for req_file in req_files[:3]:  # Check up to 3 requirements files
            try:
                content = req_file.read_text()
                if 'flask' in content.lower():
                    architecture['frameworks'].append('Flask')
                if 'django' in content.lower():
                    architecture['frameworks'].append('Django')
                if 'fastapi' in content.lower():
                    architecture['frameworks'].append('FastAPI')
            except:
                pass
        
        # Detect databases
        all_files_sample = list(self.project_path.rglob('*'))[:200]
        db_keywords = {
            'postgres': 'PostgreSQL',
            'mysql': 'MySQL',
            'mongodb': 'MongoDB',
            'redis': 'Redis',
            'elasticsearch': 'Elasticsearch',
            'sqlite': 'SQLite'
        }
        
        for file_path in all_files_sample:
            if file_path.is_file() and file_path.suffix in ['.py', '.js', '.go', '.yml', '.yaml', '.env']:
                try:
                    content = file_path.read_text().lower()
                    for keyword, db_name in db_keywords.items():
                        if keyword in content and db_name not in architecture['databases']:
                            architecture['databases'].append(db_name)
                except:
                    pass
        
        # Detect API style
        if any('graphql' in str(f).lower() for f in all_files_sample):
            architecture['api_style'] = 'GraphQL'
        elif any('.proto' in str(f) for f in all_files_sample):
            architecture['api_style'] = 'gRPC'
        else:
            architecture['api_style'] = 'REST'
        
        return architecture
    
    def _generate_summary(self, file_stats, security, quality, architecture):
        """Generate executive summary"""
        total_files = sum(file_stats['files_by_language'].values())
        
        summary = {
            'total_source_files': total_files,
            'primary_language': file_stats['files_by_language'].most_common(1)[0][0] if file_stats['files_by_language'] else 'Unknown',
            'languages_found': len(file_stats['files_by_language']),
            'security_issues': {
                'total': security['total_issues'],
                'critical': security['severity_summary'].get('CRITICAL', 0),
                'high': security['severity_summary'].get('HIGH', 0),
                'medium': security['severity_summary'].get('MEDIUM', 0),
                'low': security['severity_summary'].get('LOW', 0)
            },
            'code_quality_issues': quality['total_issues'],
            'architecture_type': architecture['structure'],
            'services_found': len(architecture['services']),
            'frameworks_detected': architecture['frameworks']
        }
        
        # Key findings
        findings = []
        
        if summary['security_issues']['critical'] > 0:
            findings.append(f"🚨 {summary['security_issues']['critical']} critical security issues found")
        
        if architecture['structure'] == 'microservices':
            findings.append(f"✅ Microservices architecture detected with {len(architecture['services'])} services")
        elif architecture['structure'] == 'monolithic':
            findings.append("📦 Monolithic architecture - consider breaking into services")
        
        if quality['languages'].get('Python', {}).get('python2_code', 0) > 0:
            findings.append("⚠️ Python 2 code detected - migration needed")
        
        summary['key_findings'] = findings
        
        return summary
    
    def generate_report(self):
        """Generate markdown report"""
        r = self.results
        s = r['summary']
        
        report = [
            f"# Multi-Language Code Analysis Report",
            f"\n**Project**: {r['project_path']}",
            f"**Date**: {r['scan_time']}",
            f"\n## Executive Summary",
            f"- **Primary Language**: {s['primary_language']}",
            f"- **Total Languages**: {s['languages_found']}",
            f"- **Total Source Files**: {s['total_source_files']:,}",
            f"- **Architecture**: {s['architecture_type'].title()}",
            f"- **Security Issues**: {s['security_issues']['total']} total",
            f"  - Critical: {s['security_issues']['critical']}",
            f"  - High: {s['security_issues']['high']}",
            f"  - Medium: {s['security_issues']['medium']}",
            f"- **Code Quality Issues**: {s['code_quality_issues']}",
        ]
        
        if s['key_findings']:
            report.append("\n### Key Findings")
            for finding in s['key_findings']:
                report.append(f"- {finding}")
        
        # File statistics
        report.append(f"\n## File Statistics")
        report.append(f"- Total files scanned: {r['file_statistics']['total_files']:,}")
        report.append(f"- Files excluded: {r['file_statistics']['excluded_files']:,}")
        report.append(f"- Files analyzed: {r['file_statistics']['analyzed_files']:,}")
        
        report.append("\n### Language Distribution")
        for lang, count in r['file_statistics']['files_by_language'].most_common(10):
            lines = r['file_statistics']['language_lines'].get(lang, 0)
            if lines > 0:
                report.append(f"- **{lang}**: {count:,} files ({lines:,} lines)")
            else:
                report.append(f"- **{lang}**: {count:,} files")
        
        # Security scan
        if r['security_scan']['total_issues'] > 0:
            report.append(f"\n## Security Scan Results")
            report.append(f"Files scanned: {r['security_scan']['files_scanned']}")
            
            for issue_type, issues in r['security_scan']['issues'].items():
                if issues:
                    report.append(f"\n### {issue_type.replace('_', ' ').title()}")
                    report.append(f"Found {len(issues)} instances:")
                    for issue in issues[:3]:  # Show first 3
                        report.append(f"- `{issue['file']}:{issue['line']}` [{issue['severity']}]")
                    if len(issues) > 3:
                        report.append(f"- ... and {len(issues) - 3} more")
        
        # Code quality
        report.append(f"\n## Code Quality Analysis")
        for lang, metrics in r['code_quality']['languages'].items():
            report.append(f"\n### {lang}")
            report.append(f"- Files analyzed: {metrics['files_analyzed']}")
            for key, value in metrics.items():
                if key not in ['files_analyzed', 'issues_found'] and value > 0:
                    report.append(f"- {key.replace('_', ' ').title()}: {value}")
        
        # Architecture
        arch = r['architecture']
        report.append(f"\n## Architecture Analysis")
        report.append(f"- **Structure**: {arch['structure'].title()}")
        report.append(f"- **API Style**: {arch['api_style']}")
        
        if arch['services']:
            report.append(f"\n### Services/Modules Found ({len(arch['services'])})")
            for service in arch['services'][:10]:
                report.append(f"- {service}")
        
        if arch['frameworks']:
            report.append(f"\n### Frameworks Detected")
            for framework in arch['frameworks']:
                report.append(f"- {framework}")
        
        if arch['databases']:
            report.append(f"\n### Databases Detected")
            for db in arch['databases']:
                report.append(f"- {db}")
        
        # Recommendations
        report.append(f"\n## Recommendations")
        
        if s['security_issues']['critical'] > 0:
            report.append(f"1. **URGENT**: Fix {s['security_issues']['critical']} critical security issues immediately")
        
        if s['security_issues']['high'] > 0:
            report.append(f"2. Address {s['security_issues']['high']} high-severity security issues")
        
        if s['architecture_type'] == 'monolithic' and s['total_source_files'] > 500:
            report.append("3. Consider breaking the monolith into microservices")
        
        if 'Python' in r['code_quality']['languages'] and r['code_quality']['languages']['Python'].get('python2_code', 0) > 0:
            report.append("4. Migrate Python 2 code to Python 3")
        
        if s['code_quality_issues'] > 50:
            report.append("5. Implement code quality standards and linting")
        
        return '\n'.join(report)


def main():
    import sys

    # Get project path
    project_path = sys.argv[1] if len(sys.argv) > 1 else '.'
    
    # Run analysis
    analyzer = SimpleMultiLanguageAnalyzer(project_path)
    
    try:
        results = analyzer.analyze()
        
        # Save results
        output_prefix = sys.argv[2] if len(sys.argv) > 2 else 'simple_analysis'
        
        # Save JSON
        with open(f'{output_prefix}_results.json', 'w') as f:
            json.dump(results, f, indent=2, default=str)
        
        # Generate and save report
        report = analyzer.generate_report()
        with open(f'{output_prefix}_report.md', 'w') as f:
            f.write(report)
        
        # Print report
        print("\n" + "="*60)
        print(report)
        print("="*60)
        
        print(f"\n✅ Analysis complete!")
        print(f"📊 Results saved to: {output_prefix}_results.json")
        print(f"📄 Report saved to: {output_prefix}_report.md")
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()