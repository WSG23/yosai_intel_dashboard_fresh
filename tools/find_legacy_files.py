import argparse
import datetime
import os
import re
import subprocess
from pathlib import Path
from typing import Iterable, Tuple

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

IGNORE_DIRS = {".git", "node_modules", "__pycache__", "venv"}


def matches_patterns(path: Path) -> str | None:
    for pat in PATTERNS:
        if re.search(pat, path.name, re.IGNORECASE):
            return pat
    return None


def last_commit_timestamp(path: Path) -> int | None:
    try:
        result = subprocess.run(
            ["git", "log", "-1", "--format=%ct", "--", str(path)],
            capture_output=True,
            text=True,
            check=True,
        )
        if result.stdout.strip():
            return int(result.stdout.strip())
    except subprocess.CalledProcessError:
        return None
    return None


def older_than_months(timestamp: int, months: int) -> bool:
    dt = datetime.datetime.fromtimestamp(timestamp)
    return (datetime.datetime.now() - dt).days >= months * 30


def scan(root: Path) -> Iterable[Tuple[Path, list[str]]]:
    for dirpath, dirnames, filenames in os.walk(root):
        dirnames[:] = [d for d in dirnames if d not in IGNORE_DIRS]
        for filename in filenames:
            path = Path(dirpath) / filename
            reasons: list[str] = []
            match = matches_patterns(path)
            if match:
                reasons.append(f"name matches '{match}'")
            try:
                mtime = path.stat().st_mtime
                if older_than_months(int(mtime), 6):
                    reasons.append("no modification in last 6 months")
            except OSError:
                pass

            commit_ts = last_commit_timestamp(path)
            if commit_ts and older_than_months(commit_ts, 12):
                reasons.append("no commit in last year")

            if reasons:
                yield path, reasons


def main() -> None:
    parser = argparse.ArgumentParser(description="Find potential legacy files")
    parser.add_argument("--delete", action="store_true", help="Delete matched files")
    args = parser.parse_args()

    for path, reasons in scan(Path(".")):
        print(f"{path}  # {', '.join(reasons)}")
        if args.delete:
            try:
                os.remove(path)
                print(f"Removed {path}")
            except OSError as exc:
                print(f"Failed to remove {path}: {exc}")


if __name__ == "__main__":
    main()
