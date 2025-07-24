#!/usr/bin/env python3
"""Generate static API documentation portal using Redoc."""
from __future__ import annotations

from pathlib import Path
import subprocess

# Mapping of spec file to (slug, title) for the generated docs
SPECS: dict[str, tuple[str, str]] = {
    "api/openapi/yosai-api-v2.yaml": ("v2", "Yōsai Intel Dashboard API v2"),
    "api/contracts/access-event.yaml": ("v1", "Access Event Service v1"),
    "api/contracts/analytics.yaml": ("analytics", "Analytics Service v1"),
}


def bundle(spec: str, out_path: Path) -> None:
    """Bundle a spec into a standalone HTML file using redoc-cli."""
    subprocess.run(
        ["npx", "redoc-cli", "bundle", spec, "-o", str(out_path)],
        check=True,
    )


def main() -> None:
    out_dir = Path("docs/portal")
    out_dir.mkdir(parents=True, exist_ok=True)

    links: list[tuple[str, str]] = []

    for spec, (slug, title) in SPECS.items():
        dest = out_dir / f"{slug}.html"
        bundle(spec, dest)
        links.append((title, dest.name))

    index_lines = [
        "<html>",
        "<body>",
        "<h1>API Documentation</h1>",
        "<ul>",
    ]
    for title, fname in links:
        index_lines.append(f'  <li><a href="{fname}">{title}</a></li>')
    index_lines += ["</ul>", "</body>", "</html>"]
    (out_dir / "index.html").write_text("\n".join(index_lines))


if __name__ == "__main__":
    main()
