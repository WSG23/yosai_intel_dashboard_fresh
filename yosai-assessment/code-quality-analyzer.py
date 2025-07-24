#!/usr/bin/env python3
"""
Code Quality Analysis Module for Yōsai Intel Dashboard
Specific code pattern detection and quality metrics
"""

import ast
import re
from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import Dict, List, Optional, Set, Tuple


class CodeSmell(Enum):
    """Types of code quality issues"""
    HARDCODED_SECRET = "Hardcoded Secret"
    SYNC_IN_ASYNC = "Synchronous Code in Async Context"
    BROAD_EXCEPTION = "Broad Exception Handling"
    MISSING_ERROR_HANDLING = "Missing Error Handling"
    SQL_INJECTION_RISK = "SQL Injection Risk"
    MISSING_INPUT_VALIDATION = "Missing Input Validation"
    INEFFICIENT_QUERY = "Inefficient Database Query"
    MISSING_TIMEOUT = "Missing Timeout Configuration"
    RESOURCE_LEAK = "Potential Resource Leak"
    RACE_CONDITION = "Potential Race Condition"


@dataclass
class CodeIssue:
    """Individual code quality issue"""
    file_path: str
    line_number: int
    smell_type: CodeSmell
    severity: str  # HIGH, MEDIUM, LOW
    description: str
    suggestion: str
    code_snippet: Optional[str] = None


class PythonAnalyzer:
    """Analyze Python code for quality issues"""
    
    def __init__(self):
        self.issues: List[CodeIssue] = []
        
    def analyze_file(self, file_path: Path) -> List[CodeIssue]:
        """Analyze a Python file for code issues"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
                
            # Parse AST
            tree = ast.parse(content, filename=str(file_path))
            
            # Run various analyzers
            self._check_hardcoded_secrets(content, file_path)
            self._check_async_patterns(tree, content, file_path)
            self._check_exception_handling(tree, content, file_path)
            self._check_sql_patterns(content, file_path)
            self._check_resource_management(tree, content, file_path)
            
            return self.issues
            
        except Exception as e:
            print(f"Error analyzing {file_path}: {e}")
            return []
            
    def _check_hardcoded_secrets(self, content: str, file_path: Path) -> None:
        """Check for hardcoded secrets"""
        patterns = [
            (r'SECRET_KEY\s*=\s*["\'][\w\-]+["\']', "Hardcoded SECRET_KEY"),
            (r'JWT_SECRET\s*=\s*["\'][^"\']+["\']', "Hardcoded JWT secret"),
            (r'password\s*=\s*["\'][^"\']+["\']', "Hardcoded password"),
            (r'api_key\s*=\s*["\'][^"\']+["\']', "Hardcoded API key"),
        ]
        
        lines = content.split('\n')
        for i, line in enumerate(lines):
            for pattern, desc in patterns:
                if re.search(pattern, line, re.IGNORECASE):
                    self.issues.append(CodeIssue(
                        file_path=str(file_path),
                        line_number=i + 1,
                        smell_type=CodeSmell.HARDCODED_SECRET,
                        severity="HIGH",
                        description=desc,
                        suggestion="Use environment variables or secret management service",
                        code_snippet=line.strip()
                    ))
                    
    def _check_async_patterns(self, tree: ast.AST, content: str, file_path: Path) -> None:
        """Check for synchronous code in async contexts"""
        
        class AsyncVisitor(ast.NodeVisitor):
            def __init__(self, analyzer):
                self.analyzer = analyzer
                self.in_async = False
                
            def visit_AsyncFunctionDef(self, node):
                old_async = self.in_async
                self.in_async = True
                self.generic_visit(node)
                self.in_async = old_async
                
            def visit_Call(self, node):
                if self.in_async:
                    # Check for sync operations in async context
                    if isinstance(node.func, ast.Attribute):
                        if node.func.attr in ['execute', 'commit', 'fetchall', 'fetchone']:
                            # Database operations without await
                            self.analyzer.issues.append(CodeIssue(
                                file_path=str(file_path),
                                line_number=node.lineno,
                                smell_type=CodeSmell.SYNC_IN_ASYNC,
                                severity="HIGH",
                                description="Synchronous database operation in async function",
                                suggestion="Use async database drivers (asyncpg, aiomysql)",
                                code_snippet=ast.get_source_segment(content, node)
                            ))
                    elif isinstance(node.func, ast.Name):
                        if node.func.id == 'run_in_executor':
                            self.analyzer.issues.append(CodeIssue(
                                file_path=str(file_path),
                                line_number=node.lineno,
                                smell_type=CodeSmell.SYNC_IN_ASYNC,
                                severity="MEDIUM",
                                description="Using run_in_executor for sync code",
                                suggestion="Refactor to use native async operations",
                                code_snippet=ast.get_source_segment(content, node)
                            ))
                self.generic_visit(node)
                
        visitor = AsyncVisitor(self)
        visitor.visit(tree)
        
    def _check_exception_handling(self, tree: ast.AST, content: str, file_path: Path) -> None:
        """Check for broad exception handling"""
        
        class ExceptionVisitor(ast.NodeVisitor):
            def __init__(self, analyzer):
                self.analyzer = analyzer
                
            def visit_ExceptHandler(self, node):
                if node.type is None or (isinstance(node.type, ast.Name) and node.type.id == 'Exception'):
                    self.analyzer.issues.append(CodeIssue(
                        file_path=str(file_path),
                        line_number=node.lineno,
                        smell_type=CodeSmell.BROAD_EXCEPTION,
                        severity="MEDIUM",
                        description="Catching broad Exception class",
                        suggestion="Catch specific exceptions and handle appropriately",
                        code_snippet=f"except {node.type.id if node.type else ''}: ..."
                    ))
                self.generic_visit(node)
                
        visitor = ExceptionVisitor(self)
        visitor.visit(tree)
        
    def _check_sql_patterns(self, content: str, file_path: Path) -> None:
        """Check for SQL injection risks"""
        patterns = [
            (r'execute\s*\(\s*["\'].*%s.*["\'].*%', "String formatting in SQL"),
            (r'execute\s*\(\s*f["\']', "F-string in SQL query"),
            (r'execute\s*\([^,)]*\+[^,)]*\)', "String concatenation in SQL"),
        ]
        
        lines = content.split('\n')
        for i, line in enumerate(lines):
            for pattern, desc in patterns:
                if re.search(pattern, line):
                    self.issues.append(CodeIssue(
                        file_path=str(file_path),
                        line_number=i + 1,
                        smell_type=CodeSmell.SQL_INJECTION_RISK,
                        severity="HIGH",
                        description=desc,
                        suggestion="Use parameterized queries",
                        code_snippet=line.strip()
                    ))
                    
    def _check_resource_management(self, tree: ast.AST, content: str, file_path: Path) -> None:
        """Check for resource management issues"""
        
        class ResourceVisitor(ast.NodeVisitor):
            def __init__(self, analyzer):
                self.analyzer = analyzer
                
            def visit_Call(self, node):
                # Check for missing context managers
                if isinstance(node.func, ast.Name):
                    if node.func.id in ['open', 'connect', 'Client']:
                        # Check if it's not in a with statement
                        parent = getattr(node, 'parent', None)
                        if not isinstance(parent, ast.withitem):
                            self.analyzer.issues.append(CodeIssue(
                                file_path=str(file_path),
                                line_number=node.lineno,
                                smell_type=CodeSmell.RESOURCE_LEAK,
                                severity="HIGH",
                                description=f"Resource {node.func.id} not using context manager",
                                suggestion="Use 'with' statement for resource management",
                                code_snippet=ast.get_source_segment(content, node)
                            ))
                            
                # Check for missing timeouts
                if isinstance(node.func, ast.Attribute):
                    if node.func.attr in ['get', 'post', 'request']:
                        has_timeout = any(
                            kw.arg == 'timeout' for kw in node.keywords
                        )
                        if not has_timeout:
                            self.analyzer.issues.append(CodeIssue(
                                file_path=str(file_path),
                                line_number=node.lineno,
                                smell_type=CodeSmell.MISSING_TIMEOUT,
                                severity="MEDIUM",
                                description="HTTP request without timeout",
                                suggestion="Add timeout parameter to prevent hanging",
                                code_snippet=ast.get_source_segment(content, node)
                            ))
                            
                self.generic_visit(node)
                
        visitor = ResourceVisitor(self)
        visitor.visit(tree)


class GoAnalyzer:
    """Analyze Go code for quality issues"""
    
    def __init__(self):
        self.issues: List[CodeIssue] = []
        
    def analyze_file(self, file_path: Path) -> List[CodeIssue]:
        """Analyze a Go file for code issues"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
                
            self._check_error_handling(content, file_path)
            self._check_concurrency_patterns(content, file_path)
            self._check_resource_management(content, file_path)
            self._check_security_patterns(content, file_path)
            
            return self.issues
            
        except Exception as e:
            print(f"Error analyzing {file_path}: {e}")
            return []
            
    def _check_error_handling(self, content: str, file_path: Path) -> None:
        """Check for ignored errors"""
        patterns = [
            (r'_\s*,\s*:=', "Explicitly ignored error"),
            (r':=.*\n[^i]*if.*err.*nil', "Error not checked immediately"),
        ]
        
        lines = content.split('\n')
        for i, line in enumerate(lines):
            if '_ =' in line or '_, err :=' in line:
                self.issues.append(CodeIssue(
                    file_path=str(file_path),
                    line_number=i + 1,
                    smell_type=CodeSmell.MISSING_ERROR_HANDLING,
                    severity="HIGH",
                    description="Ignored error return value",
                    suggestion="Handle errors appropriately",
                    code_snippet=line.strip()
                ))
                
    def _check_concurrency_patterns(self, content: str, file_path: Path) -> None:
        """Check for concurrency issues"""
        lines = content.split('\n')
        
        # Check for goroutine leaks
        for i, line in enumerate(lines):
            if 'go func' in line:
                # Check if there's a proper channel or waitgroup
                context = '\n'.join(lines[max(0, i-5):min(len(lines), i+10)])
                if 'defer' not in context and 'Done()' not in context:
                    self.issues.append(CodeIssue(
                        file_path=str(file_path),
                        line_number=i + 1,
                        smell_type=CodeSmell.RESOURCE_LEAK,
                        severity="HIGH",
                        description="Potential goroutine leak",
                        suggestion="Use sync.WaitGroup or ensure goroutine termination",
                        code_snippet=line.strip()
                    ))
                    
    def _check_resource_management(self, content: str, file_path: Path) -> None:
        """Check for resource management issues"""
        patterns = [
            (r'\.Open\(.*\)', "File opened without defer close"),
            (r'\.Dial\(.*\)', "Connection without defer close"),
        ]
        
        lines = content.split('\n')
        for i, line in enumerate(lines):
            for pattern, desc in patterns:
                if re.search(pattern, line):
                    # Check if next lines have defer Close()
                    if i + 1 < len(lines) and 'defer' not in lines[i + 1]:
                        self.issues.append(CodeIssue(
                            file_path=str(file_path),
                            line_number=i + 1,
                            smell_type=CodeSmell.RESOURCE_LEAK,
                            severity="HIGH",
                            description=desc,
                            suggestion="Add defer Close() after resource opening",
                            code_snippet=line.strip()
                        ))
                        
    def _check_security_patterns(self, content: str, file_path: Path) -> None:
        """Check for security issues"""
        patterns = [
            (r'fmt\.Sprintf.*WHERE.*%s', "SQL injection risk"),
            (r'http\.ListenAndServe.*:0\.0\.0\.0', "Binding to all interfaces"),
            (r'InsecureSkipVerify.*true', "TLS verification disabled"),
        ]
        
        lines = content.split('\n')
        for i, line in enumerate(lines):
            for pattern, desc in patterns:
                if re.search(pattern, line):
                    self.issues.append(CodeIssue(
                        file_path=str(file_path),
                        line_number=i + 1,
                        smell_type=CodeSmell.SQL_INJECTION_RISK if 'SQL' in desc else CodeSmell.HARDCODED_SECRET,
                        severity="HIGH",
                        description=desc,
                        suggestion="Fix security vulnerability",
                        code_snippet=line.strip()
                    ))


class ConfigAnalyzer:
    """Analyze configuration files for issues"""
    
    def __init__(self):
        self.issues: List[CodeIssue] = []
        
    def analyze_yaml(self, file_path: Path) -> List[CodeIssue]:
        """Analyze YAML configuration files"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
                
            self._check_production_config(content, file_path)
            self._check_security_config(content, file_path)
            
            return self.issues
            
        except Exception as e:
            print(f"Error analyzing {file_path}: {e}")
            return []
            
    def _check_production_config(self, content: str, file_path: Path) -> None:
        """Check production configuration settings"""
        lines = content.split('\n')
        
        critical_settings = {
            'debug:': ('true', "Debug mode enabled in production"),
            'log_level:': ('DEBUG', "Verbose logging in production"),
            'ssl_mode:': ('disable', "SSL disabled for database"),
            'rate_limiting_enabled:': ('false', "Rate limiting disabled"),
        }
        
        for i, line in enumerate(lines):
            for setting, (bad_value, desc) in critical_settings.items():
                if setting in line and bad_value in line:
                    self.issues.append(CodeIssue(
                        file_path=str(file_path),
                        line_number=i + 1,
                        smell_type=CodeSmell.HARDCODED_SECRET,
                        severity="HIGH",
                        description=desc,
                        suggestion="Update production configuration",
                        code_snippet=line.strip()
                    ))
                    
    def _check_security_config(self, content: str, file_path: Path) -> None:
        """Check security-related configuration"""
        if 'production' in str(file_path).lower():
            # Check for missing security headers
            security_headers = ['cors_enabled', 'rate_limiting', 'session_timeout']
            for header in security_headers:
                if header not in content:
                    self.issues.append(CodeIssue(
                        file_path=str(file_path),
                        line_number=0,
                        smell_type=CodeSmell.MISSING_INPUT_VALIDATION,
                        severity="MEDIUM",
                        description=f"Missing {header} configuration",
                        suggestion=f"Add {header} to production config",
                        code_snippet="N/A"
                    ))


class CodeQualityReport:
    """Generate code quality reports"""
    
    def __init__(self):
        self.python_analyzer = PythonAnalyzer()
        self.go_analyzer = GoAnalyzer()
        self.config_analyzer = ConfigAnalyzer()
        
    def analyze_codebase(self, root_path: Path) -> Dict[str, Any]:
        """Analyze entire codebase"""
        all_issues = []
        
        # Analyze Python files
        for py_file in root_path.rglob("*.py"):
            if "test_" not in py_file.name and "__pycache__" not in str(py_file):
                issues = self.python_analyzer.analyze_file(py_file)
                all_issues.extend(issues)
                
        # Analyze Go files
        for go_file in root_path.rglob("*.go"):
            if "_test.go" not in go_file.name:
                issues = self.go_analyzer.analyze_file(go_file)
                all_issues.extend(issues)
                
        # Analyze config files
        for yaml_file in root_path.rglob("*.yaml"):
            issues = self.config_analyzer.analyze_yaml(yaml_file)
            all_issues.extend(issues)
            
        return self._generate_report(all_issues)
        
    def _generate_report(self, issues: List[CodeIssue]) -> Dict[str, Any]:
        """Generate quality report from issues"""
        # Group by severity
        by_severity = {
            "HIGH": [],
            "MEDIUM": [],
            "LOW": []
        }
        
        for issue in issues:
            by_severity[issue.severity].append({
                "file": issue.file_path,
                "line": issue.line_number,
                "type": issue.smell_type.value,
                "description": issue.description,
                "suggestion": issue.suggestion,
                "snippet": issue.code_snippet
            })
            
        # Group by smell type
        by_type = {}
        for issue in issues:
            smell_type = issue.smell_type.value
            if smell_type not in by_type:
                by_type[smell_type] = []
            by_type[smell_type].append({
                "file": issue.file_path,
                "line": issue.line_number,
                "severity": issue.severity
            })
            
        # Calculate metrics
        total_issues = len(issues)
        high_severity = len(by_severity["HIGH"])
        code_health_score = max(0, 100 - (high_severity * 10) - (len(by_severity["MEDIUM"]) * 3))
        
        return {
            "total_issues": total_issues,
            "issues_by_severity": by_severity,
            "issues_by_type": by_type,
            "code_health_score": code_health_score,
            "top_concerns": self._get_top_concerns(by_type),
            "recommended_fixes": self._get_recommended_fixes(issues)
        }
        
    def _get_top_concerns(self, by_type: Dict[str, List]) -> List[str]:
        """Get top code quality concerns"""
        concerns = []
        
        if CodeSmell.HARDCODED_SECRET.value in by_type:
            concerns.append("Critical: Hardcoded secrets found in codebase")
            
        if CodeSmell.SQL_INJECTION_RISK.value in by_type:
            concerns.append("Critical: SQL injection vulnerabilities detected")
            
        if CodeSmell.SYNC_IN_ASYNC.value in by_type:
            concerns.append("Performance: Synchronous operations in async code")
            
        if CodeSmell.RESOURCE_LEAK.value in by_type:
            concerns.append("Reliability: Potential resource leaks detected")
            
        return concerns[:5]  # Top 5 concerns
        
    def _get_recommended_fixes(self, issues: List[CodeIssue]) -> List[Dict[str, str]]:
        """Get prioritized fix recommendations"""
        # Prioritize by severity and group similar issues
        high_priority = [i for i in issues if i.severity == "HIGH"]
        
        recommendations = []
        seen_types = set()
        
        for issue in high_priority[:10]:  # Top 10 recommendations
            if issue.smell_type not in seen_types:
                seen_types.add(issue.smell_type)
                recommendations.append({
                    "issue_type": issue.smell_type.value,
                    "action": issue.suggestion,
                    "example_file": issue.file_path,
                    "severity": issue.severity
                })
                
        return recommendations


# Integration function for main assessment
def analyze_code_quality(project_path: Path = Path(".")) -> Dict[str, Any]:
    """Run code quality analysis and return results"""
    analyzer = CodeQualityReport()
    return analyzer.analyze_codebase(project_path)


if __name__ == "__main__":
    # Example usage
    report = analyze_code_quality()
    print(f"Code Health Score: {report['code_health_score']}/100")
    print(f"Total Issues: {report['total_issues']}")
    print("\nTop Concerns:")
    for concern in report['top_concerns']:
        print(f"  - {concern}")