from pathlib import Path
from typing import List

from .base_analyzer import BaseAnalyzer, IssueType, QualityIssue

MAX_LINE_LENGTH = 88


class StyleAnalyzer(BaseAnalyzer):
    """Analyzes code style and formatting"""

    def __init__(self) -> None:
        self.metrics = {"max_line_length": 0}

    def analyze(self, file_path: Path) -> List[QualityIssue]:
        issues = []
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                lines = f.readlines()

            for i, line in enumerate(lines, 1):
                line_length = len(line.rstrip())
                if line_length > self.metrics["max_line_length"]:
                    self.metrics["max_line_length"] = line_length

                if line_length > MAX_LINE_LENGTH:
                    issues.append(
                        QualityIssue(
                            file_path=str(file_path),
                            line_number=i,
                            issue_type=IssueType.STYLE,
                            severity="info",
                            message=f"Line too long: {line_length} chars",
                            rule="line_length",
                            suggestion=(
                                f"Break long lines (max: {MAX_LINE_LENGTH} chars)"
                            ),
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
        return self.metrics.copy()
