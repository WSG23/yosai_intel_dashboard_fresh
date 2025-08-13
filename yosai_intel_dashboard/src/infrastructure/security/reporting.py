"""Aggregate security scan results and generate a report."""

from __future__ import annotations

import json
import os
from pathlib import Path

OUTPUT_MD = Path("security-report.md")
OUTPUT_HTML = Path("security-report.html")

SEVERITY_ORDER = {"LOW": 0, "MEDIUM": 1, "HIGH": 2, "CRITICAL": 3}


def load_result(path: Path) -> dict | None:
    p = Path(path)
    if not p.exists():
        return None
    with p.open(encoding="utf-8") as fh:
        return json.load(fh)


def main() -> None:
    reports = [
        r
        for r in [
            load_result(Path("security_code_scan.json")),
            load_result(Path("security_secrets_scan.json")),
        ]
        if r
    ]

    highest = "LOW"
    lines = ["# Security Scan Report", ""]
    for rep in reports:
        severity = rep.get("severity", "LOW").upper()
        if SEVERITY_ORDER.get(severity, 0) > SEVERITY_ORDER[highest]:
            highest = severity
        lines.append(f"## {rep['name']}")
        lines.append(f"Severity: {severity}")
        if rep.get("findings"):
            lines.append("Findings:")
            lines.append("```")
            lines.append(json.dumps(rep["findings"], indent=2))
            lines.append("```")
        if rep.get("remediation"):
            lines.append(f"Remediation: {rep['remediation']}")
        lines.append("")

    markdown = "\n".join(lines)
    OUTPUT_MD.write_text(markdown, encoding="utf-8")
    OUTPUT_HTML.write_text("<html><body>" + markdown.replace("\n", "<br>") + "</body></html>", encoding="utf-8")

    # communicate severity back to GitHub Actions
    gha_output = os.environ.get("GITHUB_OUTPUT")
    if gha_output:
        gha_path = Path(gha_output)
        with gha_path.open("a", encoding="utf-8") as fh:
            fh.write(f"severity={highest}\n")

    if highest in {"HIGH", "CRITICAL"}:
        raise SystemExit(1)


if __name__ == "__main__":
    main()

