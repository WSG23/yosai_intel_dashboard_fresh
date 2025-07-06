from abc import ABC, abstractmethod
from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List


class QualityLevel(Enum):
    EXCELLENT = "excellent"
    GOOD = "good"
    NEEDS_IMPROVEMENT = "needs_improvement"
    POOR = "poor"


class IssueType(Enum):
    STYLE = "style"
    COMPLEXITY = "complexity"
    MAINTAINABILITY = "maintainability"
    PERFORMANCE = "performance"
    SECURITY = "security"
    DOCUMENTATION = "documentation"
    TESTING = "testing"


@dataclass
class QualityIssue:
    file_path: str
    line_number: int
    issue_type: IssueType
    severity: str
    message: str
    rule: str
    suggestion: str = None


class BaseAnalyzer(ABC):
    """Base class for all code analyzers"""

    @abstractmethod
    def analyze(self, file_path: Path) -> List[QualityIssue]:
        pass

    @abstractmethod
    def get_metrics(self) -> Dict[str, Any]:
        pass
