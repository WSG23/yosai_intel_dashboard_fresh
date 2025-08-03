from __future__ import annotations

import inspect
from typing import Any, Dict, List, Set, Tuple, Type

from flask import Flask
from pydantic import BaseModel


def _extract_permission(func: Any) -> str | None:
    """Return permission requirement attached to *func* if present."""
    for attr in ("required_permission", "permission"):
        if hasattr(func, attr):
            value = getattr(func, attr)
            if isinstance(value, str):
                return value
    for f in (func, getattr(func, "__wrapped__", None)):
        if not f:
            continue
        closure = getattr(f, "__closure__", None)
        code = getattr(f, "__code__", None)
        if closure and code:
            for name, cell in zip(code.co_freevars, closure):
                if name == "permission" and isinstance(cell.cell_contents, str):
                    return cell.cell_contents
    return None


class FlaskIntrospector:
    """Collect routing information from a :class:`flask.Flask` application."""

    def collect(self, app: Flask) -> Tuple[Dict[str, Dict[str, Any]], List[Type[BaseModel]]]:
        paths: Dict[str, Dict[str, Any]] = {}
        models: Set[Type[BaseModel]] = set()

        for rule in app.url_map.iter_rules():
            methods = [m for m in rule.methods if m not in {"HEAD", "OPTIONS"}]
            if not methods:
                continue
            view = app.view_functions[rule.endpoint]

            perm = _extract_permission(view)

            sig = inspect.signature(view)
            request_model: Type[BaseModel] | None = None
            for param in sig.parameters.values():
                ann = param.annotation
                if inspect.isclass(ann) and issubclass(ann, BaseModel):
                    request_model = ann
                    models.add(ann)
                    break
            response_model: Type[BaseModel] | None = None
            ann = sig.return_annotation
            if inspect.isclass(ann) and issubclass(ann, BaseModel):
                response_model = ann
                models.add(ann)

            ops: Dict[str, Any] = {}
            for method in methods:
                op: Dict[str, Any] = {
                    "summary": view.__name__,
                    "responses": {
                        "401": {"$ref": "#/components/responses/UnauthorizedError"},
                        "403": {"$ref": "#/components/responses/ForbiddenError"},
                    },
                }
                if perm:
                    op.setdefault("security", [{"BearerAuth": []}])
                    op["x-permissions"] = [perm]
                if request_model:
                    op["requestBody"] = {
                        "content": {
                            "application/json": {
                                "schema": {"$ref": f"#/components/schemas/{request_model.__name__}"}
                            }
                        }
                    }
                if response_model:
                    op["responses"]["200"] = {
                        "description": "Successful Response",
                        "content": {
                            "application/json": {
                                "schema": {"$ref": f"#/components/schemas/{response_model.__name__}"}
                            }
                        },
                    }
                ops[method.lower()] = op

            paths[str(rule.rule)] = ops

        return paths, list(models)
