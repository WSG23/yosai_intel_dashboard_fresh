"""Simple domain boundary validation tool."""

from __future__ import annotations

import ast
from pathlib import Path
from typing import Dict, List


class DomainBoundaryValidator:
    DOMAIN_RULES = {
        "components/": {"cannot_import_from": []},
        "services/": {"cannot_import_from": ["components."]},
    }
    IGNORED_IMPORTS = {
        "yosai_intel_dashboard.src.components.plugin_adapter",
        "yosai_intel_dashboard.src.components.file_preview",
    }

    def validate_file(self, path: Path) -> Dict[str, List[str]]:
        violations = {}
        domain = self._get_domain(path)
        rules = self.DOMAIN_RULES.get(domain)
        if not rules:
            return violations
        with open(path, encoding="utf-8") as f:
            tree = ast.parse(f.read())
        imports = [
            self._module_name(n)
            for n in ast.walk(tree)
            if isinstance(n, (ast.Import, ast.ImportFrom))
        ]
        for imp in imports:
            if imp in self.IGNORED_IMPORTS:
                continue
            for forbidden in rules["cannot_import_from"]:
                if imp.startswith(forbidden):
                    violations.setdefault(domain, []).append(f"{path}: {imp}")
        return violations

    def _module_name(self, node: ast.AST) -> str:
        if isinstance(node, ast.Import):
            return node.names[0].name
        elif isinstance(node, ast.ImportFrom):
            return node.module or ""
        return ""

    def _get_domain(self, path: Path) -> str:
        parts = path.parts
        if "components" in parts:
            return "components/"
        if "services" in parts:
            return "services/"
        return ""

    def validate_all(self) -> Dict[str, List[str]]:
        violations: Dict[str, List[str]] = {}
        for py_file in Path(".").rglob("*.py"):
            if "tests" in py_file.parts:
                continue
            v = self.validate_file(py_file)
            for k, lst in v.items():
                violations.setdefault(k, []).extend(lst)
        return violations


if __name__ == "__main__":
    validator = DomainBoundaryValidator()
    result = validator.validate_all()
    if result:
        for domain, issues in result.items():
            print(f"\n{domain} violations:")
            for issue in issues:
                print("  -", issue)
    else:
        print("✅ All domain boundaries respected!")
