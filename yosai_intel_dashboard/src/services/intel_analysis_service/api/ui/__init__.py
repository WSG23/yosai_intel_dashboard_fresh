"""GraphQL gateway exposing graph queries for the intel analysis service."""

from fastapi import APIRouter
from strawberry.fastapi import GraphQLRouter

from .schema import schema

router = APIRouter()
router.include_router(GraphQLRouter(schema), prefix="/graphql", tags=["graph"])
