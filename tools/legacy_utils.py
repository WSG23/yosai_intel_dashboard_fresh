# Utility functions shared by legacy detection tools.
from __future__ import annotations

import os
import re
import subprocess
from datetime import datetime
from pathlib import Path
from typing import Iterable, Iterator, Tuple, Set

PATTERNS = [
    r"old",
    r"backup",
    r"copy",
    r"temp",
    r"tmp",
    r"deprecated",
    r"legacy",
    r"_v\d+",
    r"\d{4}",
    r"\.bak$",
    r"\.old$",
    r"\.orig$",
]

IGNORE_DIRS: Set[str] = {".git", "node_modules", "__pycache__", "venv"}


def matches_patterns(path: Path, patterns: Iterable[str] = PATTERNS) -> str | None:
    """Return the pattern that matches the file name or ``None``."""
    for pat in patterns:
        if re.search(pat, path.name, re.IGNORECASE):
            return pat
    return None


def iter_files(root: Path, ignore_dirs: Set[str] = IGNORE_DIRS) -> Iterator[Path]:
    """Yield all files under ``root`` skipping ``ignore_dirs``."""
    for dirpath, dirnames, filenames in os.walk(root):
        dirnames[:] = [d for d in dirnames if d not in ignore_dirs]
        for filename in filenames:
            yield Path(dirpath) / filename


def git_last_commit(path: Path, *, cwd: Path | None = None) -> datetime | None:
    """Return the last commit datetime for ``path`` if available."""
    try:
        result = subprocess.run(
            ["git", "log", "-1", "--format=%ct", "--", str(path)],
            capture_output=True,
            text=True,
            check=True,
            cwd=cwd,
        )
        if result.stdout.strip():
            return datetime.fromtimestamp(int(result.stdout.strip()))
    except subprocess.CalledProcessError:
        return None
    return None


def older_than(dt: datetime, months: int) -> bool:
    """Return ``True`` if ``dt`` is older than the given number of months."""
    return (datetime.now() - dt).days >= months * 30


def scan_legacy_files(
    root: Path,
    *,
    ignore_dirs: Set[str] = IGNORE_DIRS,
    patterns: Iterable[str] = PATTERNS,
) -> Iterable[Tuple[Path, list[str]]]:
    """Yield files considered legacy along with the reasons."""
    for path in iter_files(root, ignore_dirs):
        reasons: list[str] = []
        match = matches_patterns(path, patterns)
        if match:
            reasons.append(f"name matches '{match}'")
        try:
            mtime = datetime.fromtimestamp(path.stat().st_mtime)
            if older_than(mtime, 6):
                reasons.append("no modification in last 6 months")
        except OSError:
            pass
        commit_dt = git_last_commit(path, cwd=root)
        if commit_dt and older_than(commit_dt, 12):
            reasons.append("no commit in last year")
        if reasons:
            yield path, reasons
