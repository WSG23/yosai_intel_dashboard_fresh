from __future__ import annotations

import inspect
from typing import Any, Dict, List, Set, Tuple, Type

from fastapi import FastAPI
from pydantic import BaseModel


def _extract_permission(func: Any) -> str | None:
    """Return permission requirement attached to *func* if present."""
    # Direct attribute
    for attr in ("required_permission", "permission"):
        if hasattr(func, attr):
            value = getattr(func, attr)
            if isinstance(value, str):
                return value
    # Inspect closures for variable named ``permission``
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


class FastAPIIntrospector:
    """Collect routing information from a :class:`fastapi.FastAPI` instance."""

    def collect(self, app: FastAPI) -> Tuple[Dict[str, Dict[str, Any]], List[Type[BaseModel]]]:
        paths: Dict[str, Dict[str, Any]] = {}
        models: Set[Type[BaseModel]] = set()

        for route in app.routes:
            methods = [m for m in getattr(route, "methods", set()) if m not in {"HEAD", "OPTIONS"}]
            if not methods:
                continue

            permissions: List[str] = []
            dependant = getattr(route, "dependant", None)
            if dependant:
                for dep in dependant.dependencies:
                    perm = _extract_permission(dep.call)
                    if perm:
                        permissions.append(perm)

            request_models: List[Type[BaseModel]] = []
            if dependant:
                for param in dependant.body_params:
                    ann = param.annotation
                    if inspect.isclass(ann) and issubclass(ann, BaseModel):
                        request_models.append(ann)
                        models.add(ann)

            response_model: Type[BaseModel] | None = None
            rm = getattr(route, "response_model", None)
            if inspect.isclass(rm) and issubclass(rm, BaseModel):
                response_model = rm
                models.add(rm)

            operations: Dict[str, Any] = {}
            for method in methods:
                op: Dict[str, Any] = {
                    "summary": route.name or "",
                    "responses": {
                        "401": {"$ref": "#/components/responses/UnauthorizedError"},
                        "403": {"$ref": "#/components/responses/ForbiddenError"},
                    },
                }
                if permissions:
                    op.setdefault("security", [{"BearerAuth": []}])
                    op["x-permissions"] = permissions
                if request_models:
                    model = request_models[0]
                    op["requestBody"] = {
                        "content": {
                            "application/json": {
                                "schema": {"$ref": f"#/components/schemas/{model.__name__}"}
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
                operations[method.lower()] = op

            paths[route.path] = operations

        return paths, list(models)
