from __future__ import annotations

import json
from pathlib import Path
from typing import List, Type

from apispec import APISpec
from pydantic import BaseModel

# Allow running as a script without installing as a package
import sys
CURRENT_DIR = Path(__file__).resolve().parent
if str(CURRENT_DIR) not in sys.path:
    sys.path.append(str(CURRENT_DIR))

from fastapi_introspector import FastAPIIntrospector
from flask_introspector import FlaskIntrospector


PROJECT_ROOT = Path(__file__).resolve().parents[2]


def _load_fastapi_apps() -> List[object]:
    apps: List[object] = []
    try:
        from yosai_intel_dashboard.src.services.analytics.async_api import app as analytics_app

        apps.append(analytics_app)
    except Exception:
        pass
    return apps


def _load_flask_apps() -> List[object]:
    apps: List[object] = []
    try:
        from api import app as flask_app  # type: ignore

        apps.append(flask_app)
    except Exception:
        pass
    return apps


def main() -> None:
    spec = APISpec(
        title="Yosai API",
        version="1.0.0",
        openapi_version="3.0.2",
        info={"description": "Auto-generated API documentation."},
        plugins=[],
    )

    # Common components
    spec.components.security_scheme(
        "BearerAuth",
        {"type": "http", "scheme": "bearer", "bearerFormat": "JWT"},
    )
    spec.components.response(
        "UnauthorizedError", {"description": "JWT token missing or invalid"}
    )
    spec.components.response(
        "ForbiddenError", {"description": "Permission denied"}
    )

    models: List[Type[BaseModel]] = []

    for app in _load_fastapi_apps():
        try:
            paths, m = FastAPIIntrospector().collect(app)
            models.extend(m)
            for path, operations in paths.items():
                spec.path(path=path, operations=operations)
        except Exception as exc:  # pragma: no cover - introspection best effort
            print(f"FastAPI introspection failed: {exc}")

    for app in _load_flask_apps():
        try:
            paths, m = FlaskIntrospector().collect(app)
            models.extend(m)
            for path, operations in paths.items():
                spec.path(path=path, operations=operations)
        except Exception as exc:  # pragma: no cover - introspection best effort
            print(f"Flask introspection failed: {exc}")

    # Register collected schemas
    for model in {m for m in models}:
        spec.components.schema(
            model.__name__, schema=model.model_json_schema(ref_template="#/components/schemas/{model}")
        )

    output_path = PROJECT_ROOT / "docs" / "openapi.json"
    output_path.write_text(json.dumps(spec.to_dict(), indent=2))
    print(f"OpenAPI spec written to {output_path}")


if __name__ == "__main__":
    main()
