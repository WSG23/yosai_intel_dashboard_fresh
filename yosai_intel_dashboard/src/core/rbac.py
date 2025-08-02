from __future__ import annotations

"""Simple RBAC service and decorators."""

import asyncio
import inspect
import logging
import os
import threading
from functools import wraps
from typing import Callable, List, Optional

import asyncpg
import redis.asyncio as redis
from flask import current_app, session

logger = logging.getLogger(__name__)


class RBACService:
    """Role based access control service using asyncpg and Redis."""

    def __init__(
        self,
        pool: asyncpg.Pool,
        redis_client: Optional[redis.Redis] = None,
        ttl: int = 60,
    ) -> None:
        self.pool = pool
        self.redis = redis_client
        self.ttl = ttl

    # ------------------------------------------------------------------
    async def get_roles(self, user_id: str) -> List[str]:
        cache_key = f"roles:{user_id}"
        if self.redis is not None:
            try:
                data = await self.redis.get(cache_key)
                if data is not None:
                    return data.decode("utf-8").split(",")
            except Exception as exc:  # pragma: no cover - best effort
                logger.warning(f"Redis get failed for {cache_key}: {exc}")
        rows = await self.pool.fetch(
            "SELECT role FROM user_roles WHERE user_id=$1", user_id
        )
        roles = [r["role"] for r in rows]
        if self.redis is not None:
            try:
                await self.redis.setex(cache_key, self.ttl, ",".join(roles))
            except Exception as exc:  # pragma: no cover - best effort
                logger.warning(f"Redis set failed for {cache_key}: {exc}")
        return roles

    # ------------------------------------------------------------------
    async def get_permissions(self, user_id: str) -> List[str]:
        cache_key = f"perms:{user_id}"
        if self.redis is not None:
            try:
                data = await self.redis.get(cache_key)
                if data is not None:
                    return data.decode("utf-8").split(",")
            except Exception as exc:  # pragma: no cover - best effort
                logger.warning(f"Redis get failed for {cache_key}: {exc}")
        rows = await self.pool.fetch(
            "SELECT permission FROM user_permissions WHERE user_id=$1", user_id
        )
        perms = [r["permission"] for r in rows]
        if self.redis is not None:
            try:
                await self.redis.setex(cache_key, self.ttl, ",".join(perms))
            except Exception as exc:  # pragma: no cover - best effort
                logger.warning(f"Redis set failed for {cache_key}: {exc}")
        return perms

    # ------------------------------------------------------------------
    async def has_role(self, user_id: str, role: str) -> bool:
        roles = await self.get_roles(user_id)
        return role in roles

    async def has_permission(self, user_id: str, permission: str) -> bool:
        perms = await self.get_permissions(user_id)
        return permission in perms


# Helper factory ---------------------------------------------------------------
async def create_rbac_service() -> RBACService:
    """Create and initialize :class:`RBACService` using app configuration."""
    from yosai_intel_dashboard.src.infrastructure.config import get_database_config

    db_cfg = get_database_config()
    pool = await asyncpg.create_pool(dsn=db_cfg.get_connection_string())

    redis_client: Optional[redis.Redis] = None
    try:
        redis_client = redis.Redis(
            host=os.getenv("REDIS_HOST", "localhost"),
            port=int(os.getenv("REDIS_PORT", "6379")),
            db=int(os.getenv("REDIS_DB", "0")),
        )
        await redis_client.ping()
    except Exception:  # pragma: no cover - best effort
        redis_client = None

    return RBACService(pool, redis_client)


# Decorators -------------------------------------------------------------------
def _fail_response() -> tuple[str, int]:
    try:
        from dash.exceptions import PreventUpdate

        raise PreventUpdate
    except Exception:
        return "Forbidden", 403


_rbac_loop: asyncio.AbstractEventLoop | None = None
_rbac_thread: threading.Thread | None = None


def _ensure_loop() -> asyncio.AbstractEventLoop:
    """Return a long-lived event loop running in a background thread."""
    global _rbac_loop, _rbac_thread
    if _rbac_loop is None or _rbac_loop.is_closed():
        _rbac_loop = asyncio.new_event_loop()
        _rbac_thread = threading.Thread(
            target=_rbac_loop.run_forever, name="rbac-loop", daemon=True
        )
        _rbac_thread.start()
    return _rbac_loop


def _run_sync(coro: asyncio.Future) -> any:
    """Execute *coro* using a shared background loop."""
    try:
        loop = asyncio.get_running_loop()
    except RuntimeError:
        loop = _ensure_loop()
        return asyncio.run_coroutine_threadsafe(coro, loop).result()
    else:
        if loop.is_running():
            raise RuntimeError("_run_sync cannot be called from a running event loop")
        return loop.run_until_complete(coro)


def require_role(role: str) -> Callable[[Callable[..., any]], Callable[..., any]]:
    """Ensure the current user has *role* before calling the function."""

    def decorator(func: Callable[..., any]) -> Callable[..., any]:
        if inspect.iscoroutinefunction(func):

            @wraps(func)
            async def async_wrapper(*args, **kwargs):
                service: RBACService | None = current_app.config.get("RBAC_SERVICE")
                if service is None:
                    return await func(*args, **kwargs)
                user_id = session.get("user_id")
                if not user_id or not await service.has_role(user_id, role):
                    return _fail_response()
                return await func(*args, **kwargs)

            return async_wrapper

        @wraps(func)
        def sync_wrapper(*args, **kwargs):
            service: RBACService | None = current_app.config.get("RBAC_SERVICE")
            if service is None:
                return func(*args, **kwargs)
            user_id = session.get("user_id")
            if not user_id or not _run_sync(service.has_role(user_id, role)):
                return _fail_response()
            return func(*args, **kwargs)

        return sync_wrapper

    return decorator


def require_permission(
    permission: str,
) -> Callable[[Callable[..., any]], Callable[..., any]]:
    """Ensure the current user has *permission* before calling the function."""

    def decorator(func: Callable[..., any]) -> Callable[..., any]:
        if inspect.iscoroutinefunction(func):

            @wraps(func)
            async def async_wrapper(*args, **kwargs):
                service: RBACService | None = current_app.config.get("RBAC_SERVICE")
                if service is None:
                    return await func(*args, **kwargs)
                user_id = session.get("user_id")
                if not user_id or not await service.has_permission(user_id, permission):
                    return _fail_response()
                return await func(*args, **kwargs)

            return async_wrapper

        @wraps(func)
        def sync_wrapper(*args, **kwargs):
            service: RBACService | None = current_app.config.get("RBAC_SERVICE")
            if service is None:
                return func(*args, **kwargs)
            user_id = session.get("user_id")
            if not user_id or not _run_sync(
                service.has_permission(user_id, permission)
            ):
                return _fail_response()
            return func(*args, **kwargs)

        return sync_wrapper

    return decorator


__all__ = [
    "RBACService",
    "create_rbac_service",
    "require_role",
    "require_permission",
]
