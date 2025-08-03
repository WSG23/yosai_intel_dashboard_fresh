#!/usr/bin/env python3
"""Generate Markdown API reference from OpenAPI spec."""
from __future__ import annotations

import json
from pathlib import Path
from textwrap import dedent

SPEC_PATH = Path("docs/openapi.json")
OUTPUT_PATH = Path("docs/api_reference.md")

# Additional endpoints not present in the base spec
EXTRA_PATHS = {
    "/v1/metrics/performance": {
        "get": {"summary": "Return sample performance metrics."}
    },
    "/v1/metrics/drift": {"get": {"summary": "Return sample drift statistics."}},
    "/v1/metrics/feature-importance": {
        "get": {"summary": "Return sample feature importances."}
    },
}


def load_spec() -> dict:
    spec = json.loads(SPEC_PATH.read_text(encoding="utf-8"))
    spec.setdefault("paths", {}).update(EXTRA_PATHS)
    return spec


def endpoint_block(method: str, path: str, summary: str) -> str:
    method_upper = method.upper()
    function_name = path.strip("/").replace("/", "_").replace("-", "_") or "root"
    return dedent(
        f"""
        ### `{method_upper} {path}`

        **Summary:** {summary}

        **FastAPI**
        ```python
        from fastapi import FastAPI

        app = FastAPI()

        @app.{method}("{path}")
        async def {function_name}():
            ...
        ```

        **Flask**
        ```python
        from flask import Flask, jsonify

        app = Flask(__name__)

        @app.route("{path}", methods=["{method_upper}"])
        def {function_name}():
            return jsonify()
        ```

        **curl**
        ```bash
        curl -X {method_upper} http://localhost:8000{path}
        ```
        """
    )


def build_doc(spec: dict) -> str:
    health_blocks: list[str] = []
    metrics_blocks: list[str] = []

    for path, methods in sorted(spec.get("paths", {}).items()):
        for method, meta in methods.items():
            summary = meta.get("summary", "").strip() or ""
            block = endpoint_block(method, path, summary)
            if path.startswith("/v1/metrics"):
                metrics_blocks.append(block)
            else:
                health_blocks.append(block)

    lines = ["# API Reference\n"]
    if health_blocks:
        lines.append("## Health-Check Endpoints\n")
        lines.extend(health_blocks)
    if metrics_blocks:
        lines.append("## Metrics Endpoints\n")
        lines.extend(metrics_blocks)
    return "\n".join(lines)


def main() -> None:
    spec = load_spec()
    OUTPUT_PATH.write_text(build_doc(spec), encoding="utf-8")


if __name__ == "__main__":
    main()
