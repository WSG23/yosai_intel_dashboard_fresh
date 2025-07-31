from __future__ import annotations

"""Asynchronous repository for analytics events."""

from typing import AsyncIterator, Iterable, Sequence

from sqlalchemy import delete, select, update
from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from config import get_database_config
from services.timescale.models import AccessEvent, Base

# ---------------------------------------------------------------------------
# Engine and session factory
# ---------------------------------------------------------------------------
_db_cfg = get_database_config()
_async_url = _db_cfg.get_connection_string().replace(
    "postgresql://", "postgresql+asyncpg://"
)
engine: AsyncEngine = create_async_engine(
    _async_url,
    pool_size=_db_cfg.async_pool_min_size,
    max_overflow=max(_db_cfg.async_pool_max_size - _db_cfg.async_pool_min_size, 0),
    pool_timeout=_db_cfg.async_connection_timeout,
)

SessionFactory = async_sessionmaker(engine, expire_on_commit=False)


class AsyncEventRepository:
    """CRUD interface for :class:`~services.timescale.models.AccessEvent`."""

    def __init__(
        self,
        session_factory: async_sessionmaker[AsyncSession] | None = None,
    ) -> None:
        self._session_factory = session_factory or SessionFactory

    async def create_event(self, event: AccessEvent) -> None:
        """Persist a new access event."""
        async with self._session_factory() as session:
            async with session.begin():
                session.add(event)

    async def get_events(self, limit: int | None = None) -> Sequence[AccessEvent]:
        """Return recent events ordered by time descending."""
        async with self._session_factory() as session:
            stmt = select(AccessEvent).order_by(AccessEvent.time.desc())
            if limit is not None:
                stmt = stmt.limit(limit)
            result = await session.execute(stmt)
            return result.scalars().all()

    async def update_event(self, event_id: str, **fields: object) -> int:
        """Update event ``event_id`` with ``fields`` returning affected rows."""
        async with self._session_factory() as session:
            async with session.begin():
                result = await session.execute(
                    update(AccessEvent)
                    .where(AccessEvent.event_id == event_id)
                    .values(**fields)
                )
                return result.rowcount

    async def delete_event(self, event_id: str) -> int:
        """Delete event ``event_id`` returning affected rows."""
        async with self._session_factory() as session:
            async with session.begin():
                result = await session.execute(
                    delete(AccessEvent).where(AccessEvent.event_id == event_id)
                )
                return result.rowcount

    async def bulk_insert_events(self, events: Iterable[AccessEvent]) -> None:
        """Insert multiple events efficiently."""
        events_list = list(events)
        if not events_list:
            return
        async with self._session_factory() as session:
            async with session.begin():
                session.add_all(events_list)

    async def stream_event_ids(self) -> AsyncIterator[str]:
        """Yield event IDs using ``stream_scalars``."""
        async with self._session_factory() as session:
            async for event_id in session.stream_scalars(
                select(AccessEvent.event_id).order_by(AccessEvent.time)
            ):
                yield str(event_id)


async def init_models() -> None:
    """Create database tables for the mapped models."""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


__all__ = [
    "AsyncEventRepository",
    "engine",
    "SessionFactory",
    "init_models",
]
