from typing import List, Dict, Any
from pathlib import Path
from analyzers.ast_analyzer import ASTAnalyzer
from analyzers.style_analyzer import StyleAnalyzer
from analyzers.base_analyzer import QualityIssue, QualityLevel

class CodeQualityOrchestrator:
    """Orchestrates multiple analyzers for comprehensive code quality analysis"""

    def __init__(self, project_root: str = "."):
        self.project_root = Path(project_root)
        self.analyzers = [
            ASTAnalyzer(),
            StyleAnalyzer(),
        ]

    def analyze_project(self) -> Dict[str, Any]:
        python_files = list(self.project_root.rglob("*.py"))
        python_files = [f for f in python_files if self._should_include(f)]

        all_issues: List[QualityIssue] = []
        combined_metrics: Dict[str, Any] = {}

        for file_path in python_files:
            for analyzer in self.analyzers:
                issues = analyzer.analyze(file_path)
                all_issues.extend(issues)

                metrics = analyzer.get_metrics()
                for key, value in metrics.items():
                    if key not in combined_metrics:
                        combined_metrics[key] = value
                    elif isinstance(value, list):
                        combined_metrics[key].extend(value)
                    elif isinstance(value, (int, float)):
                        combined_metrics[key] += value

        return {
            'issues': all_issues,
            'metrics': combined_metrics,
            'files_analyzed': len(python_files),
            'quality_level': self._calculate_quality_level(all_issues)
        }

    def _should_include(self, file_path: Path) -> bool:
        skip_patterns = ['__pycache__', '.git', 'venv', 'env', '.pytest_cache']
        return not any(pattern in str(file_path) for pattern in skip_patterns)

    def _calculate_quality_level(self, issues: List[QualityIssue]) -> QualityLevel:
        if not issues:
            return QualityLevel.EXCELLENT

        error_count = sum(1 for i in issues if i.severity == "error")
        warning_count = sum(1 for i in issues if i.severity == "warning")

        if error_count > 0:
            return QualityLevel.POOR
        elif warning_count > 10:
            return QualityLevel.NEEDS_IMPROVEMENT
        elif warning_count > 5:
            return QualityLevel.GOOD
        else:
            return QualityLevel.EXCELLENT
