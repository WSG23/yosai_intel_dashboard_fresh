#!/usr/bin/env python3
"""Generate basic API documentation from OpenAPI spec."""
from __future__ import annotations

import json
from pathlib import Path

OPENAPI_PATH = Path("docs/openapi.json")
OUTPUT_MD = Path("docs/api_docs.md")
OUTPUT_PDF = Path("docs/api_docs.pdf")


def build_markdown(spec: dict) -> str:
    lines: list[str] = [
        "# API Documentation",
        "",
        "Generated from OpenAPI specification.",
        "",
    ]
    for path, methods in sorted(spec.get("paths", {}).items()):
        for method, info in methods.items():
            summary = info.get("summary", "")
            lines.append(f"## {method.upper()} {path}")
            if summary:
                lines.append(summary)
            lines.append("")
    return "\n".join(lines)


def write_pdf(text: str) -> None:
    try:
        from fpdf import FPDF  # type: ignore
    except Exception as exc:
        print(f"PDF generation skipped (missing fpdf): {exc}")
        return
    pdf = FPDF()
    pdf.set_auto_page_break(auto=True, margin=15)
    pdf.add_page()
    pdf.set_font("Arial", size=12)
    for line in text.splitlines():
        pdf.multi_cell(0, 10, line)
    pdf.output(str(OUTPUT_PDF))


def main() -> None:
    if not OPENAPI_PATH.exists():
        raise FileNotFoundError(f"OpenAPI spec not found at {OPENAPI_PATH}")
    spec = json.loads(OPENAPI_PATH.read_text())
    markdown = build_markdown(spec)
    OUTPUT_MD.write_text(markdown)
    write_pdf(markdown)
    print(f"Generated {OUTPUT_MD} and {OUTPUT_PDF}")


if __name__ == "__main__":
    main()
