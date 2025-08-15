#!/usr/bin/env python3
"""Generate a Mermaid ER diagram from SQL migration files.

The script scans SQL files in the ``migrations`` directory for ``CREATE TABLE``
statements and ``REFERENCES`` clauses. It then emits a Mermaid ``erDiagram``
representation listing the foreign key relationships discovered.

Usage::

    python scripts/generate_er_diagram.py

The resulting diagram is written to ``docs/database/er_diagram.md``.
"""
from __future__ import annotations

from pathlib import Path
import re

ROOT = Path(__file__).resolve().parents[1]
MIGRATIONS = ROOT / "migrations"
OUTPUT = ROOT / "docs" / "database" / "er_diagram.md"

create_re = re.compile(r"^CREATE TABLE IF NOT EXISTS\s+(\w+)", re.IGNORECASE)
ref_re = re.compile(r"REFERENCES\s+(\w+)", re.IGNORECASE)

def main() -> None:
    tables: set[str] = set()
    relations: set[tuple[str, str]] = set()

    for sql_file in sorted(MIGRATIONS.glob("*.sql")):
        lines = sql_file.read_text().splitlines()
        current: str | None = None
        for raw in lines:
            line = raw.strip()
            m = create_re.match(line)
            if m:
                current = m.group(1)
                tables.add(current)
                continue
            if current:
                if line.startswith(")"):
                    current = None
                    continue
                ref = ref_re.search(line)
                if ref:
                    parent = ref.group(1)
                    relations.add((parent, current))

    mermaid_lines = ["# Entity Relationship Diagram", "", "Generated automatically from migrations.", "", "```mermaid", "erDiagram"]
    for parent, child in sorted(relations):
        mermaid_lines.append(f"    {parent} ||--o{{ {child} : \"\"")
    mermaid_lines.append("```")
    OUTPUT.write_text("\n".join(mermaid_lines) + "\n")
    print(f"Wrote {OUTPUT.relative_to(ROOT)}")

if __name__ == "__main__":
    main()
