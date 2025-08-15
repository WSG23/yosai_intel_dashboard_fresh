from __future__ import annotations

"""Context manager utilities for database transactions.

The :func:`with_transaction` helper wraps a SQLAlchemy session in a
transactional scope.  It commits on success, rolls back on error and
always closes the session ensuring that connections are returned to the
pool.  The function works with both synchronous :class:`~sqlalchemy.orm.Session`
and asynchronous :class:`~sqlalchemy.ext.asyncio.AsyncSession` objects.
"""

from contextlib import asynccontextmanager, contextmanager
from typing import AsyncIterator, Iterator

try:  # Optional import so tests without SQLAlchemy still run
    from sqlalchemy.ext.asyncio import AsyncSession  # type: ignore
    from sqlalchemy.orm import Session  # type: ignore
except Exception:  # pragma: no cover - SQLAlchemy not installed
    AsyncSession = object  # type: ignore
    Session = object  # type: ignore


@contextmanager
def _transaction_sync(session: Session) -> Iterator[Session]:
    """Transactional scope for synchronous sessions."""
    try:
        yield session
        session.commit()
    except Exception:  # pragma: no cover - passthrough to caller
        session.rollback()
        raise
    finally:
        session.close()


@asynccontextmanager
async def _transaction_async(session: AsyncSession) -> AsyncIterator[AsyncSession]:
    """Transactional scope for asynchronous sessions."""
    try:
        yield session
        await session.commit()
    except Exception:  # pragma: no cover - passthrough to caller
        await session.rollback()
        raise
    finally:
        await session.close()


def with_transaction(session):
    """Return a context manager wrapping *session* in a transaction.

    The returned object can be used with ``with`` for synchronous sessions or
    ``async with`` for :class:`~sqlalchemy.ext.asyncio.AsyncSession` instances.
    """

    if isinstance(session, AsyncSession):
        return _transaction_async(session)
    return _transaction_sync(session)


__all__ = ["with_transaction"]
