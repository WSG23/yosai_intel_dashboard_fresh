from typing import List
from pathlib import Path
from .base_analyzer import BaseAnalyzer, QualityIssue, IssueType


class StyleAnalyzer(BaseAnalyzer):
    """Analyzes code style and formatting"""

    def analyze(self, file_path: Path) -> List[QualityIssue]:
        issues = []
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                lines = f.readlines()

            for i, line in enumerate(lines, 1):
                if len(line.rstrip()) > 120:
                    issues.append(
                        QualityIssue(
                            file_path=str(file_path),
                            line_number=i,
                            issue_type=IssueType.STYLE,
                            severity="info",
                            message=f"Line too long: {len(line.rstrip())} chars",
                            rule="line_length",
                            suggestion="Break long lines (max: 120 chars)",
                        )
                    )

                if line.rstrip() != line.rstrip("\n"):
                    issues.append(
                        QualityIssue(
                            file_path=str(file_path),
                            line_number=i,
                            issue_type=IssueType.STYLE,
                            severity="info",
                            message="Trailing whitespace",
                            rule="trailing_whitespace",
                            suggestion="Remove trailing whitespace",
                        )
                    )

        except Exception:
            pass
        return issues

    def get_metrics(self):
        return {}
