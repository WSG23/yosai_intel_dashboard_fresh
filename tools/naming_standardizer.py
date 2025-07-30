"""Utilities for enforcing naming conventions across the project."""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path
from typing import Dict, List

import yaml

from tools.robust_file_reader import safe_read_text

_CAMEL_RE = re.compile(r"\b[a-z]+[A-Z][A-Za-z0-9]*\b")


def camel_to_snake(name: str) -> str:
    """Convert ``name`` from camelCase to snake_case."""
    s1 = re.sub("(.)([A-Z][a-z]+)", r"\1_\2", name)
    s2 = re.sub("([a-z0-9])([A-Z])", r"\1_\2", s1)
    return s2.lower()


# ---------------------------------------------------------------------------


def scan_for_violations(directory: str) -> Dict[str, List[str]]:
    """Return mapping of file paths to a list of camelCase names found."""
    violations: Dict[str, List[str]] = {}
    for path in Path(directory).rglob("*.py"):
        text = safe_read_text(path)
        found = [m.group(0) for m in _CAMEL_RE.finditer(text)]
        if found:
            violations[str(path)] = found
    for ext in ("*.yml", "*.yaml"):
        for path in Path(directory).rglob(ext):
            try:
                data = yaml.safe_load(safe_read_text(path)) or {}
            except Exception:
                continue
            bad_keys: List[str] = []

            def _walk(obj: object) -> None:
                if isinstance(obj, dict):
                    for k, v in obj.items():
                        if re.search(r"[A-Z]", k):
                            bad_keys.append(k)
                        _walk(v)
                elif isinstance(obj, list):
                    for item in obj:
                        _walk(item)

            _walk(data)
            if bad_keys:
                violations.setdefault(str(path), []).extend(bad_keys)
    return violations


# ---------------------------------------------------------------------------


def fix_camel_case_variables(file_path: str) -> None:
    """Convert camelCase variable names in ``file_path`` to snake_case."""
    path = Path(file_path)
    text = safe_read_text(path)

    def repl(match: re.Match[str]) -> str:
        return camel_to_snake(match.group(0))

    new_text = _CAMEL_RE.sub(repl, text)
    path.write_text(new_text)


# ---------------------------------------------------------------------------


def standardize_config_keys(config_file: str) -> None:
    """Rewrite YAML ``config_file`` with snake_case keys."""
    path = Path(config_file)
    try:
        data = yaml.safe_load(safe_read_text(path))
    except Exception:
        return

    def _convert(obj: object) -> object:
        if isinstance(obj, dict):
            new: Dict[str, object] = {}
            for k, v in obj.items():
                new[camel_to_snake(k)] = _convert(v)
            return new
        if isinstance(obj, list):
            return [_convert(i) for i in obj]
        return obj

    new_data = _convert(data)
    path.write_text(yaml.dump(new_data, sort_keys=False))


# ---------------------------------------------------------------------------


def _cli() -> None:
    parser = argparse.ArgumentParser(description="Naming standardization helper")
    sub = parser.add_subparsers(dest="cmd")

    scan = sub.add_parser("scan", help="scan directory for naming violations")
    scan.add_argument("path", nargs="?", default=".")

    fix = sub.add_parser("fix", help="fix camelCase variables in a file or directory")
    fix.add_argument("path")
    fix.add_argument("--config", action="store_true", help="treat file as YAML config")

    args = parser.parse_args()
    if args.cmd == "scan":
        report = scan_for_violations(args.path)
        print(json.dumps(report, indent=2))
    elif args.cmd == "fix":
        target = Path(args.path)
        if args.config or target.suffix in {".yml", ".yaml"}:
            if target.is_dir():
                for f in target.rglob("*.yml"):
                    standardize_config_keys(str(f))
                for f in target.rglob("*.yaml"):
                    standardize_config_keys(str(f))
            else:
                standardize_config_keys(str(target))
        else:
            if target.is_dir():
                for f in target.rglob("*.py"):
                    fix_camel_case_variables(str(f))
            else:
                fix_camel_case_variables(str(target))
    else:
        parser.print_help()


if __name__ == "__main__":
    _cli()
