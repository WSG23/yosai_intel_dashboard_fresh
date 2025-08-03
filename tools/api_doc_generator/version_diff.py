#!/usr/bin/env python3
"""Utility to diff OpenAPI specifications and output changelog.

This script compares a newly generated OpenAPI spec with a previous
version and produces a Markdown changelog showing added, removed and
modified endpoints. It is intended to be used after generating a new
OpenAPI document so that API changes can be reviewed easily.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Dict, Iterable, List, Tuple


Endpoint = Tuple[str, str]  # (path, method)


def _load_spec(path: Path) -> Dict:
    """Load OpenAPI spec from *path*.

    If the file does not exist, an empty specification is returned.
    """
    if not path.exists():
        return {}
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


def _extract_endpoints(spec: Dict) -> Dict[Endpoint, Dict]:
    """Return mapping of (path, method) -> endpoint definition."""
    endpoints: Dict[Endpoint, Dict] = {}
    for path, methods in spec.get("paths", {}).items():
        for method, details in methods.items():
            # Skip specification extensions (keys starting with "x-")
            if method.startswith("x-"):
                continue
            endpoints[(path, method.lower())] = details
    return endpoints


def _format_endpoint(endpoint: Endpoint) -> str:
    path, method = endpoint
    return f"{method.upper()} {path}"


def diff_specs(prev_spec: Dict, new_spec: Dict) -> Dict[str, List[str]]:
    """Compute differences between two specs.

    Returns a dictionary with keys ``added``, ``removed`` and ``modified``
    each containing a list of formatted endpoint strings.
    """
    prev_endpoints = _extract_endpoints(prev_spec)
    new_endpoints = _extract_endpoints(new_spec)

    added = sorted(
        _format_endpoint(ep) for ep in new_endpoints.keys() if ep not in prev_endpoints
    )
    removed = sorted(
        _format_endpoint(ep) for ep in prev_endpoints.keys() if ep not in new_endpoints
    )
    modified = sorted(
        _format_endpoint(ep)
        for ep in new_endpoints.keys()
        if ep in prev_endpoints and new_endpoints[ep] != prev_endpoints[ep]
    )

    return {"added": added, "removed": removed, "modified": modified}


def write_changelog(diff: Dict[str, List[str]], output: Path) -> None:
    """Write the changelog in Markdown format to *output* path."""
    lines: List[str] = ["# API Changes", ""]
    for key in ("added", "removed", "modified"):
        lines.append(f"## {key.capitalize()}")
        items = diff[key]
        if items:
            lines.extend(f"- `{item}`" for item in items)
        else:
            lines.append("None")
        lines.append("")
    output.write_text("\n".join(lines), encoding="utf-8")


def main(argv: Iterable[str] | None = None) -> None:
    parser = argparse.ArgumentParser(
        description="Compare OpenAPI specs and output changelog of added/removed/modified endpoints."
    )
    parser.add_argument(
        "new_spec", nargs="?", default="docs/openapi.json", help="Path to newly generated spec"
    )
    parser.add_argument(
        "--prev", default="docs/openapi_prev.json", help="Path to previous spec file"
    )
    parser.add_argument(
        "--out", default="docs/api_changes.md", help="Path for changelog output"
    )
    args = parser.parse_args(list(argv) if argv is not None else None)

    new_spec = _load_spec(Path(args.new_spec))
    prev_spec = _load_spec(Path(args.prev))
    diff = diff_specs(prev_spec, new_spec)
    write_changelog(diff, Path(args.out))


if __name__ == "__main__":
    main()
