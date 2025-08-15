"""FastAPI service exposing REST and GraphQL endpoints for intel analysis.

This module provides a minimal web service that can be expanded by the
intel analysis team.  It exposes a simple REST endpoint and a GraphQL
schema to demonstrate how both styles of APIs can coexist within the
service.  The GraphQL endpoint relies on ``graphene`` which is an optional
dependency.  If the package is not installed the endpoint will raise an
``ImportError`` when the application starts.
"""

from __future__ import annotations

from fastapi import Depends, FastAPI
from yosai_intel_dashboard.src.services.security import requires_role

try:
    import graphene
    from fastapi.graphql import GraphQLRouter
except Exception:  # pragma: no cover - graphene optional in test env
    graphene = None  # type: ignore
    GraphQLRouter = None  # type: ignore


app = FastAPI(title="Intel Analysis Service")


@app.get("/api/v1/status")
def status(_: None = Depends(requires_role("analyst"))) -> dict[str, str]:
    """Basic health endpoint for REST clients."""

    return {"status": "ok"}


if graphene is not None:

    class Query(graphene.ObjectType):
        """GraphQL schema exposing a simple hello field."""

        hello = graphene.String(description="A friendly greeting")

        def resolve_hello(self, info):  # pragma: no cover - thin wrapper
            return "Hello from GraphQL"

    app.include_router(
        GraphQLRouter(schema=graphene.Schema(query=Query)),
        prefix="/api/v1/graphql",
    )
