#!/usr/bin/env python3
"""Detect usage of legacy modules and dependencies.

This script walks the project tree, parses Python files using ``ast`` and
reports imports of deprecated modules or objects. The list of deprecated
modules/dependencies is defined in a YAML rules file.
"""

from __future__ import annotations

import argparse
import ast
import json
from pathlib import Path
from typing import Dict, Iterable, List, Optional

import yaml

DEFAULT_RULES_FILE = Path("tools/legacy_rules.yaml")


class LegacyCodeDetector:
    """Scan Python files and requirements for legacy usage."""

    def __init__(self, rules_path: Optional[Path] = None) -> None:
        self.rules_path = rules_path or DEFAULT_RULES_FILE
        self.rules = {
            "deprecated_imports": ["services.analytics.data_loader"],
            "deprecated_objects": ["DataLoadingService"],
            "deprecated_dependencies": [],
        }
        if self.rules_path.exists():
            self._load_rules(self.rules_path)

    # ---------------------------------------------------------
    def _load_rules(self, path: Path) -> None:
        data = yaml.safe_load(path.read_text()) or {}
        for key in self.rules:
            if key in data:
                self.rules[key].extend(data[key])

    # ---------------------------------------------------------
    def scan_file(self, path: Path) -> List[str]:
        issues: List[str] = []
        try:
            tree = ast.parse(path.read_text(encoding="utf-8"))
        except Exception:
            return issues

        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    full_name = alias.name
                    issues.extend(self._check_name(full_name))
                    issues.extend(self._check_object(alias.name))
            elif isinstance(node, ast.ImportFrom):
                module = node.module or ""
                for alias in node.names:
                    full_name = f"{module}.{alias.name}" if module else alias.name
                    issues.extend(self._check_name(full_name))
                    issues.extend(self._check_object(alias.name))
        return issues

    def _check_name(self, name: str) -> Iterable[str]:
        for mod in self.rules["deprecated_imports"]:
            if name == mod or name.startswith(mod + "."):
                return [f"deprecated import: {name}"]
        return []

    def _check_object(self, name: str) -> Iterable[str]:
        if name in self.rules["deprecated_objects"]:
            return [f"deprecated object: {name}"]
        return []

    # ---------------------------------------------------------
    def scan_directory(self, root: Path) -> Dict[str, List[str]]:
        results: Dict[str, List[str]] = {}
        for file in root.rglob("*.py"):
            if file.is_file():
                issues = self.scan_file(file)
                if issues:
                    results[str(file)] = issues
        return results

    # ---------------------------------------------------------
    def check_requirements(self, req_path: Path) -> List[str]:
        issues: List[str] = []
        if not req_path.exists():
            return issues
        lines = [l.strip() for l in req_path.read_text().splitlines() if l.strip() and not l.startswith("#")]
        for dep in self.rules["deprecated_dependencies"]:
            for line in lines:
                pkg = line.split("==")[0]
                if pkg == dep:
                    issues.append(f"deprecated dependency: {dep}")
        return issues


def _parse_args(argv: Optional[Iterable[str]] = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Detect legacy modules")
    parser.add_argument("path", nargs="?", default=".", help="directory to scan")
    parser.add_argument("--rules", type=Path, default=DEFAULT_RULES_FILE, help="rules YAML file")
    parser.add_argument("--format", choices=["text", "json"], default="text")
    parser.add_argument("--check-requirements", action="store_true", help="inspect requirements.txt")
    return parser.parse_args(list(argv) if argv else None)


def main(argv: Optional[Iterable[str]] = None) -> int:
    args = _parse_args(argv)
    detector = LegacyCodeDetector(args.rules)
    root = Path(args.path)
    report = detector.scan_directory(root)

    if args.check_requirements:
        req_issues = detector.check_requirements(root / "requirements.txt")
        if req_issues:
            report["requirements.txt"] = req_issues

    if args.format == "json":
        print(json.dumps(report, indent=2))
    else:
        for file, issues in report.items():
            print(file)
            for issue in issues:
                print(f"  - {issue}")
    return 1 if report else 0


if __name__ == "__main__":  # pragma: no cover - CLI entry
    raise SystemExit(main())
