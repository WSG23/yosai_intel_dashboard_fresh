from pathlib import Path

import pytest

from analyzers.ast_analyzer import ASTAnalyzer
from analyzers.base_analyzer import IssueType
from analyzers.style_analyzer import StyleAnalyzer


class TestASTAnalyzer:
    """Isolated tests for AST analyzer"""

    def test_detects_high_complexity(self, tmp_path):
        test_file = tmp_path / "complex.py"
        test_file.write_text(
            """
def complex_function(x):
    if x > 0:
        if x > 10:
            if x > 20:
                if x > 30:
                    return "very high"
                return "high"
            return "medium"
        return "low"
    return "negative"
"""
        )

        analyzer = ASTAnalyzer(max_complexity=5)
        issues = analyzer.analyze(test_file)

        complexity_issues = [i for i in issues if i.issue_type == IssueType.COMPLEXITY]
        assert len(complexity_issues) == 1
        assert "complexity" in complexity_issues[0].message.lower()

    def test_metrics_tracking(self, tmp_path):
        test_file = tmp_path / "simple.py"
        test_file.write_text(
            """
class TestClass:
    def method1(self): pass
    def method2(self): pass

def function1(): pass
"""
        )

        analyzer = ASTAnalyzer()
        analyzer.analyze(test_file)
        metrics = analyzer.get_metrics()

        assert metrics["functions"] == 3  # 2 methods + 1 function
        assert metrics["classes"] == 1


class TestStyleAnalyzer:
    """Isolated tests for style analyzer"""

    def test_detects_long_lines(self, tmp_path):
        test_file = tmp_path / "long_line.py"
        long_line = "x = " + "a" * 90
        test_file.write_text(long_line)

        analyzer = StyleAnalyzer()
        issues = analyzer.analyze(test_file)

        line_length_issues = [i for i in issues if i.rule == "line_length"]
        assert len(line_length_issues) == 1

    def test_metrics_max_line_length(self, tmp_path):
        test_file = tmp_path / "metrics.py"
        long_line = "y = " + "b" * 95
        test_file.write_text("short\n" + long_line)

        analyzer = StyleAnalyzer()
        analyzer.analyze(test_file)
        metrics = analyzer.get_metrics()

        assert metrics["max_line_length"] == len(long_line)
