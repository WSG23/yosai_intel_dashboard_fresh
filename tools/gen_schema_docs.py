#!/usr/bin/env python3
"""Generate Markdown and HTML docs for Avro schemas."""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any, List

from markdown import markdown

REPO_ROOT = Path(__file__).resolve().parents[1]
SCHEMA_DIR = REPO_ROOT / "schemas" / "avro"
DOCS_DIR = REPO_ROOT / "docs" / "avro"


def type_repr(t: Any) -> str:
    """Return a human readable type representation."""
    if isinstance(t, str):
        return t
    if isinstance(t, list):
        return " | ".join(type_repr(x) for x in t)
    if isinstance(t, dict):
        base = t.get("type")
        logical = t.get("logicalType")
        if logical:
            return f"{base} ({logical})"
        return base or json.dumps(t)
    return json.dumps(t)


def make_markdown(schema: dict[str, Any]) -> str:
    lines: List[str] = [f"# {schema['name']} Schema", ""]
    if 'namespace' in schema:
        lines.append(f"Namespace: `{schema['namespace']}`\n")
    lines.append("| Field | Type | Default |")
    lines.append("|-------|------|---------|")
    for field in schema.get('fields', []):
        name = field['name']
        t = type_repr(field['type'])
        default = field.get('default')
        if default is None and 'default' not in field:
            default_repr = ""
        else:
            default_repr = json.dumps(default)
        lines.append(f"| `{name}` | `{t}` | `{default_repr}` |")
    return "\n".join(lines) + "\n"


def main() -> None:
    DOCS_DIR.mkdir(parents=True, exist_ok=True)
    schemas = sorted(SCHEMA_DIR.glob("*.avsc"))
    index_lines = ["# Avro Schemas", ""]
    for path in schemas:
        data = json.loads(path.read_text())
        md = make_markdown(data)
        base = path.stem
        md_path = DOCS_DIR / f"{base}.md"
        html_path = DOCS_DIR / f"{base}.html"
        md_path.write_text(md)
        html_path.write_text(markdown(md))
        index_lines.append(f"- [{base}]({base}.md)")
        print(f"Wrote {md_path} and {html_path}")
    (DOCS_DIR / "index.md").write_text("\n".join(index_lines) + "\n")
    (DOCS_DIR / "index.html").write_text(markdown("\n".join(index_lines)))


if __name__ == "__main__":
    main()
