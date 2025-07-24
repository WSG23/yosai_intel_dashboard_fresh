from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, List

from tailored_callback_auditor import YourSystemCallbackAuditor


class FocusedDashboardAuditor(YourSystemCallbackAuditor):
    """Auditor that only scans dashboard related directories."""

    def __init__(self, root_path: str = "."):
        super().__init__(root_path)
        # Directories/files relevant to the dashboard application
        self.target_directories: List[str] = [
            "core",
            "pages",
            "components",
            "services",
            "analytics",
            "plugins",
            "app.py",
            "wsgi.py",
        ]

    def scan_focused_codebase(self) -> Dict[str, Any]:
        """Scan only the targeted directories for callback patterns."""
        print("🔍 Starting focused callback audit...")

        existing_targets: List[Path] = []
        for target in self.target_directories:
            path = self.root_path / target
            if path.exists():
                existing_targets.append(path)

        print(f"📁 Found {len(existing_targets)} targets to analyze")

        for target in existing_targets:
            if target.is_file() and target.suffix == ".py":
                self._process_file(target)
            elif target.is_dir():
                for py_file in target.rglob("*.py"):
                    if self._should_skip_file(py_file):
                        continue
                    self._process_file(py_file)

        results = {
            "summary": self._generate_summary(),
            "conflicts": self._analyze_output_conflicts(),
            "recommendations": self._generate_consolidation_recommendations(),
            "patterns": self.patterns,
        }
        return results

    def _process_file(self, file_path: Path) -> None:
        """Analyze a single file and collect callback patterns."""
        file_patterns = self._analyze_file_comprehensively(file_path)
        for pattern in file_patterns:
            self.patterns.append(pattern)
            self.pattern_counts[pattern.pattern_type] += 1
            if pattern.component_name:
                self.namespace_usage[pattern.component_name].append(pattern.callback_id)
            for output in pattern.output_targets:
                self.output_conflicts[output].append(
                    {
                        "file": str(file_path),
                        "callback_id": pattern.callback_id,
                        "line": pattern.line_number,
                    }
                )

    def generate_dashboard_report(self, results: Dict[str, Any]) -> str:
        """Generate a concise dashboard-specific report."""
        summary = results["summary"]
        lines = [
            "🎯 DASHBOARD CALLBACK AUDIT REPORT",
            "=" * 50,
            f"Total Callbacks: {summary['total_callbacks']}",
            f"Files with Callbacks: {summary['files_with_callbacks']}",
            f"Pattern Types: {len(summary['pattern_distribution'])}",
            f"Conflicts: {summary['total_conflicts']} ("
            f"{summary['high_severity_conflicts']} critical)",
        ]
        if results.get("recommendations"):
            lines.append("\n🚀 RECOMMENDATIONS:")
            for rec in results["recommendations"]:
                lines.append(f"- {rec}")
        return "\n".join(lines)
