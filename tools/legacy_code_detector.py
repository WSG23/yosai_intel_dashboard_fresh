#!/usr/bin/env python3
"""Detect legacy or unused files in a project.

This tool searches for old or deprecated file names, checks timestamps via Git,
 and performs a simple import analysis to highlight potential dead code.
"""
from __future__ import annotations

import ast
import json
import re
import subprocess
from dataclasses import dataclass
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Set


@dataclass
class FileInfo:
    path: Path
    last_commit: datetime | None
    mtime: datetime


class LegacyDetector:
    NAME_PATTERNS = re.compile(
        r"(old|backup|copy|temp|deprecated|test|\d{4}|v\d+)|\.(bak|old|orig)$",
        re.IGNORECASE,
    )

    def __init__(self, project_root: Path) -> None:
        self.root = project_root
        self.exclude_dirs = {".git", "node_modules", "__pycache__", ".venv", "venv"}
        self.now = datetime.now()
        self.six_months = self.now - timedelta(days=180)
        self.one_year = self.now - timedelta(days=365)
        self.python_files: List[Path] = []
        self.infos: Dict[Path, FileInfo] = {}
        self.imports: Dict[Path, Set[str]] = {}
        self.defines: Set[str] = set()

    # Collect python files
    def _gather_python_files(self) -> None:
        for path in self.root.rglob("*.py"):
            if any(part in self.exclude_dirs for part in path.parts):
                continue
            self.python_files.append(path)

    # Get git timestamp for file
    def _git_last_commit(self, path: Path) -> datetime | None:
        try:
            ts = subprocess.check_output(
                ["git", "log", "-1", "--format=%ct", str(path)],
                cwd=self.root,
                stderr=subprocess.DEVNULL,
                text=True,
            ).strip()
            if ts:
                return datetime.fromtimestamp(int(ts))
        except Exception:
            pass
        return None

    def _collect_file_info(self) -> None:
        for path in self.python_files:
            mtime = datetime.fromtimestamp(path.stat().st_mtime)
            commit_ts = self._git_last_commit(path)
            self.infos[path] = FileInfo(path, commit_ts, mtime)

    # Analyze imports
    def _analyze_imports(self) -> None:
        self.module_map: Dict[str, Path] = {}
        for path in self.python_files:
            module_name = ".".join(path.relative_to(self.root).with_suffix("").parts)
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

    def detect_legacy(self) -> Dict[str, List[str]]:
        self._gather_python_files()
        self._collect_file_info()
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
            if (
                info.last_commit and info.last_commit < self.one_year
            ) or info.mtime < self.six_months:
                stale_files.append(str(path))
            module_name = ".".join(path.relative_to(self.root).with_suffix("").parts)
            if not module_usage.get(module_name):
                unused_modules.append(str(path))

        # Detect circular imports
        for file, imports in self.imports.items():
            module_name = ".".join(file.relative_to(self.root).with_suffix("").parts)
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


def main() -> None:
    import argparse

    parser = argparse.ArgumentParser(description="Scan for legacy or unused files")
    parser.add_argument("path", nargs="?", default=".", help="Project directory")
    parser.add_argument("--json", action="store_true", help="Output JSON")
    args = parser.parse_args()

    detector = LegacyDetector(Path(args.path).resolve())
    results = detector.detect_legacy()

    if args.json:
        print(json.dumps(results, indent=2))
    else:
        for key, items in results.items():
            print(f"\n{key} ({len(items)})")
            for item in items:
                print(f"  - {item}")


if __name__ == "__main__":
    main()
