import ast
from pathlib import Path
from typing import Any, Dict, List

from .base_analyzer import BaseAnalyzer, IssueType, QualityIssue


class ASTAnalyzer(BaseAnalyzer):
    """Analyzes Python AST for complexity and structure issues"""

    def __init__(self, max_complexity: int = 8, max_function_length: int = 30):
        self.max_complexity = max_complexity
        self.max_function_length = max_function_length
        self.metrics = {"functions": 0, "classes": 0, "complexity_scores": []}

    def analyze(self, file_path: Path) -> List[QualityIssue]:
        issues = []
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                tree = ast.parse(f.read())

            for node in ast.walk(tree):
                if isinstance(node, ast.FunctionDef):
                    issues.extend(self._analyze_function(node, file_path))
                elif isinstance(node, ast.ClassDef):
                    issues.extend(self._analyze_class(node, file_path))

        except Exception as e:
            issues.append(
                QualityIssue(
                    file_path=str(file_path),
                    line_number=1,
                    issue_type=IssueType.STYLE,
                    severity="error",
                    message=f"Parse error: {e}",
                    rule="parse_error",
                )
            )
        return issues

    def get_metrics(self) -> Dict[str, Any]:
        return self.metrics.copy()

    def _analyze_function(
        self, node: ast.FunctionDef, file_path: Path
    ) -> List[QualityIssue]:
        issues = []
        self.metrics["functions"] += 1

        complexity = self._calculate_complexity(node)
        self.metrics["complexity_scores"].append(complexity)

        if complexity > self.max_complexity:
            issues.append(
                QualityIssue(
                    file_path=str(file_path),
                    line_number=node.lineno,
                    issue_type=IssueType.COMPLEXITY,
                    severity="warning",
                    message=f"Function '{node.name}' complexity: {complexity}",
                    rule="max_complexity",
                    suggestion="Break into smaller functions",
                )
            )

        func_length = getattr(node, "end_lineno", node.lineno) - node.lineno + 1
        if func_length > self.max_function_length:
            issues.append(
                QualityIssue(
                    file_path=str(file_path),
                    line_number=node.lineno,
                    issue_type=IssueType.MAINTAINABILITY,
                    severity="warning",
                    message=f"Function '{node.name}' too long: {func_length} lines",
                    rule="max_function_length",
                    suggestion=f"Keep under {self.max_function_length} lines",
                )
            )

        return issues

    def _calculate_complexity(self, node: ast.FunctionDef) -> int:
        complexity = 1
        for child in ast.walk(node):
            if isinstance(
                child, (ast.If, ast.While, ast.For, ast.AsyncFor, ast.ExceptHandler)
            ):
                complexity += 1
        return complexity

    def _analyze_class(self, node: ast.ClassDef, file_path: Path) -> List[QualityIssue]:
        issues = []
        self.metrics["classes"] += 1

        if not ast.get_docstring(node):
            issues.append(
                QualityIssue(
                    file_path=str(file_path),
                    line_number=node.lineno,
                    issue_type=IssueType.DOCUMENTATION,
                    severity="info",
                    message=f"Class '{node.name}' missing docstring",
                    rule="missing_docstring",
                    suggestion="Add descriptive class docstring",
                )
            )

        return issues
