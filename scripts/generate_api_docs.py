#!/usr/bin/env python3
"""Generate Markdown and PDF API docs from the OpenAPI spec."""

import subprocess
from pathlib import Path

# Possible converter commands. Each entry should include placeholders for
# the input and output paths.
CONVERTER_CMDS = [
    ["npx", "--yes", "openapi-markdown", "-i", "{input}", "-o", "{output}"],
    ["npx", "--yes", "openapi2markdown", "{input}", "-o", "{output}"],
    ["npx", "--yes", "swagger-markdown", "-i", "{input}", "-o", "{output}"],
]


def convert_to_markdown(spec: Path, dest: Path) -> None:
    """Convert the OpenAPI spec JSON to Markdown.

    Tries a series of known converters until one succeeds.
    """
    for template in CONVERTER_CMDS:
        cmd = [
            part.replace("{input}", str(spec)).replace("{output}", str(dest))
            for part in template
        ]
        try:
            subprocess.run(cmd, check=True)
            return
        except (FileNotFoundError, subprocess.CalledProcessError):
            continue
    raise RuntimeError(
        "No OpenAPI to Markdown converter found. "
        "Install openapi-markdown, openapi2markdown, or swagger-markdown."
    )


def convert_to_pdf(md_file: Path, pdf_file: Path) -> None:
    """Convert Markdown to PDF using pandoc."""
    subprocess.run(
        [
            "pandoc",
            str(md_file),
            "-o",
            str(pdf_file),
            "--pdf-engine=wkhtmltopdf",
        ],
        check=True,
    )


def main() -> None:
    root = Path(__file__).resolve().parents[1]
    spec_path = root / "docs" / "openapi.json"
    out_dir = root / "docs" / "api"
    out_dir.mkdir(parents=True, exist_ok=True)

    md_path = out_dir / "openapi.md"
    pdf_path = out_dir / "openapi.pdf"

    convert_to_markdown(spec_path, md_path)
    convert_to_pdf(md_path, pdf_path)


if __name__ == "__main__":
    main()
