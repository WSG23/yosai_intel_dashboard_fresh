#!/usr/bin/env python3
"""Combined legacy code detector and lightweight analyzer."""
from __future__ import annotations

import ast
import json
import re
import subprocess
import logging
from collections import defaultdict
from dataclasses import dataclass
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Set

import yaml

logger = logging.getLogger(__name__)


@dataclass
class FileInfo:
    path: Path
    last_commit: datetime | None
    mtime: datetime


class LegacyCodeDetector:
    """Detect deprecated usage and analyze legacy files."""

    NAME_PATTERNS = re.compile(
        r"(old|backup|copy|temp|deprecated|test|\d{4}|v\d+)|\.(bak|old|orig)$",
        re.IGNORECASE,
    )
    DEPRECATED_OBJECTS = {"DataLoadingService"}
    DEFAULT_DEPRECATED_IMPORTS = ["services.analytics.data_loader"]

    def __init__(
        self,
        rules_path: Optional[Path] = None,
        *,
        languages: Optional[List[str]] = None,
        exclude_dirs: Optional[Set[str]] = None,
    ) -> None:
        self.rules: Dict[str, List[str]] = {}
        if rules_path and Path(rules_path).exists():
            self.rules = yaml.safe_load(Path(rules_path).read_text()) or {}
        self.deprecated_imports: List[str] = self.rules.get("deprecated_imports", [])
        self.deprecated_imports.extend(self.DEFAULT_DEPRECATED_IMPORTS)
        self.deprecated_dependencies: List[str] = self.rules.get("deprecated_dependencies", [])
        self.languages = languages or ["python"]
        self.exclude_dirs = exclude_dirs or {
            ".git",
            "node_modules",
            "__pycache__",
            ".pytest_cache",
            "venv",
            "env",
            ".venv",
            "dist",
            "build",
            ".next",
            ".idea",
            ".vscode",
            "coverage",
            "htmlcov",
            "vendor",
        }
        self.now = datetime.now()
        self.six_months = self.now - timedelta(days=180)
        self.one_year = self.now - timedelta(days=365)
        self.python_files: List[Path] = []
        self.infos: Dict[Path, FileInfo] = {}
        self.imports: Dict[Path, Set[str]] = {}
        self.defines: Set[str] = set()
        self.issues: Dict[str, List[str]] = defaultdict(list)

    # ------------------------------------------------------------------
    # helpers used by analyzer section
    def _iter_files(self, root: Path, extensions: List[str]) -> List[Path]:
        files: List[Path] = []
        for ext in extensions:
            for fpath in root.rglob(f"*{ext}"):
                if any(ex in fpath.parts for ex in self.exclude_dirs):
                    continue
                files.append(fpath)
        return files

    def _scan_files(self, root: Path) -> Dict:
        stats = {"total_files": 0, "files_by_type": defaultdict(list)}
        ext_to_lang = {
            ".py": "Python",
            ".go": "Go",
            ".js": "JavaScript",
            ".ts": "TypeScript",
            ".jsx": "JavaScript",
            ".tsx": "TypeScript",
        }
        for p in root.rglob("*"):
            if p.is_file():
                if any(ex in p.parts for ex in self.exclude_dirs):
                    continue
                stats["total_files"] += 1
                lang = ext_to_lang.get(p.suffix.lower())
                if lang:
                    stats["files_by_type"][lang].append(p)
        return stats

    def _analyze_python(self, root: Path) -> Dict:
        duplicates = defaultdict(list)
        signatures = defaultdict(list)
        unicode_issues = []
        py_files = self._iter_files(root, [".py"])
        for py_file in py_files:
            try:
                content = py_file.read_text(encoding="utf-8")
                tree = ast.parse(content)
                for node in ast.walk(tree):
                    if isinstance(node, ast.FunctionDef):
                        sig = f"{node.name}({','.join(arg.arg for arg in node.args.args)})"
                        signatures[sig].append({"file": str(py_file.relative_to(root)), "line": node.lineno})
                for match in re.finditer(r"\.encode\(\)|\.decode\(\)", content):
                    line_no = content[: match.start()].count("\n") + 1
                    unicode_issues.append({"file": str(py_file.relative_to(root)), "line": line_no})
            except Exception as exc:  # pragma: no cover - robustness
                self.issues["parse_errors"].append(f"{py_file}: {exc}")
        for sig, locs in signatures.items():
            if len(locs) > 1:
                duplicates[sig] = locs
        return {
            "files_analyzed": len(py_files),
            "duplicate_functions": len(duplicates),
            "unicode_issues": unicode_issues,
        }

    def _security_scan(self, files_by_type: Dict[str, List[Path]], root: Path) -> Dict:
        issues = defaultdict(list)
        pattern = r"(?i)(password|secret|token)\s*[:=]\s*[\"\']"
        for lang, files in files_by_type.items():
            for fpath in files[:50]:
                try:
                    content = fpath.read_text(encoding="utf-8", errors="ignore")
                    for match in re.finditer(pattern, content):
                        line_no = content[: match.start()].count("\n") + 1
                        issues[lang].append({"file": str(fpath.relative_to(root)), "line": line_no})
                except Exception:
                    continue
        total = sum(len(v) for v in issues.values())
        return {"issues": dict(issues), "total": total}

    # ------------------------------------------------------------------
    # legacy detection helpers (former LegacyDetector)
    def _gather_python_files(self, root: Path) -> None:
        self.python_files = []
        for path in root.rglob("*.py"):
            if any(part in self.exclude_dirs for part in path.parts):
                continue
            self.python_files.append(path)

    def _git_last_commit(self, root: Path, path: Path) -> datetime | None:
        try:
            ts = subprocess.check_output(
                ["git", "log", "-1", "--format=%ct", str(path)],
                cwd=root,
                stderr=subprocess.DEVNULL,
                text=True,
            ).strip()
            if ts:
                return datetime.fromtimestamp(int(ts))
        except Exception:
            pass
        return None

    def _collect_file_info(self, root: Path) -> None:
        self.infos = {}
        for path in self.python_files:
            mtime = datetime.fromtimestamp(path.stat().st_mtime)
            commit_ts = self._git_last_commit(root, path)
            self.infos[path] = FileInfo(path, commit_ts, mtime)

    def _analyze_imports(self) -> None:
        self.module_map = {}
        self.imports = {}
        self.defines = set()
        for path in self.python_files:
            module_name = ".".join(path.with_suffix("").parts)
            self.module_map[module_name] = path
            self.defines.add(module_name)

        for path in self.python_files:
            try:
                tree = ast.parse(path.read_text())
            except Exception:
                continue
            used: Set[str] = set()
            for node in ast.walk(tree):
                if isinstance(node, (ast.Import, ast.ImportFrom)):
                    for alias in node.names:
                        name = alias.name.split(".")[0]
                        used.add(name)
            self.imports[path] = used

    # ------------------------------------------------------------------
    def scan_directory(self, directory: Path) -> Dict[str, List[str]]:
        """Scan directory for deprecated imports or objects."""
        results: Dict[str, List[str]] = {}
        for path in directory.rglob("*.py"):
            if any(part in self.exclude_dirs for part in path.parts):
                continue
            content = path.read_text(encoding="utf-8", errors="ignore")
            issues: List[str] = []
            for mod in self.deprecated_imports:
                if re.search(rf"^\s*from\s+{re.escape(mod)}\s+import|^\s*import\s+{re.escape(mod)}", content, re.MULTILINE):
                    issues.append(f"deprecated import: {mod}")
            for obj in self.DEPRECATED_OBJECTS:
                if obj in content:
                    issues.append(f"deprecated object: {obj}")
            if issues:
                results[str(path)] = issues
        return results

    def check_requirements(self, req_file: Path) -> List[str]:
        issues = []
        if not req_file.exists():
            return issues
        for line in req_file.read_text().splitlines():
            pkg = line.split("==")[0].strip()
            if pkg in self.deprecated_dependencies:
                issues.append(f"deprecated dependency: {pkg}")
        return issues

    def detect_legacy(self, project_root: Path) -> Dict[str, List[str]]:
        self._gather_python_files(project_root)
        self._collect_file_info(project_root)
        self._analyze_imports()

        suspect_names = []
        stale_files = []
        unused_modules = []
        circular_pairs = []

        module_usage: Dict[str, Set[str]] = {m: set() for m in self.defines}
        for file, imports in self.imports.items():
            for mod in imports:
                if mod in module_usage:
                    module_usage[mod].add(str(file))

        for path, info in self.infos.items():
            if self.NAME_PATTERNS.search(path.name):
                suspect_names.append(str(path))
            if (info.last_commit and info.last_commit < self.one_year) or info.mtime < self.six_months:
                stale_files.append(str(path))
            module_name = ".".join(path.with_suffix("").parts)
            if not module_usage.get(module_name):
                unused_modules.append(str(path))

        for file, imports in self.imports.items():
            module_name = ".".join(file.with_suffix("").parts)
            for mod in imports:
                if mod in self.defines:
                    importer = self.module_map[mod]
                    if module_name in self.imports.get(importer, set()):
                        pair = tuple(sorted((str(file), str(importer))))
                        if pair not in circular_pairs:
                            circular_pairs.append(pair)

        return {
            "suspicious_names": suspect_names,
            "stale_files": stale_files,
            "unused_modules": unused_modules,
            "circular_imports": circular_pairs,
        }

    def run_analysis(self, project_root: Path) -> Dict:
        results = {"structure": self._scan_files(project_root)}
        if "python" in [l.lower() for l in self.languages]:
            results["python"] = self._analyze_python(project_root)
        if len(self.languages) > 1:
            results["multilanguage_security"] = self._security_scan(
                results["structure"]["files_by_type"], project_root
            )
        return results

    def generate_report(self, results: Dict, root: Path) -> str:
        lines = [f"Project: {root}", f"Total files: {results['structure']['total_files']}"]
        if "python" in results:
            py = results["python"]
            lines.append(f"Python files analyzed: {py['files_analyzed']}")
            lines.append(f"Duplicate functions: {py['duplicate_functions']}")
            lines.append(f"Unicode issues: {len(py['unicode_issues'])}")
        if "multilanguage_security" in results:
            sec = results["multilanguage_security"]
            lines.append(f"Security issues across languages: {sec['total']}")
        return "\n".join(lines)


def main() -> None:
    import argparse

    parser = argparse.ArgumentParser(description="Legacy code detector and analyzer")
    parser.add_argument("path", nargs="?", default=".", help="Project directory")
    parser.add_argument("--rules", help="Optional YAML rules file")
    parser.add_argument("--json", action="store_true", help="Output JSON")
    args = parser.parse_args()

    detector = LegacyCodeDetector(Path(args.rules) if args.rules else None)
    root = Path(args.path).resolve()
    deprecated = detector.scan_directory(root)
    legacy = detector.detect_legacy(root)
    analysis = detector.run_analysis(root)
    results = {"deprecated_usage": deprecated, "legacy": legacy, "analysis": analysis}

    if args.json:
        logger.info(json.dumps(results, indent=2, default=str))
    else:
        logger.info(detector.generate_report(analysis, root))
        for file, issues in deprecated.items():
            logger.info(f"\n{file}")
            for issue in issues:
                logger.info(f"  - {issue}")


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    main()
