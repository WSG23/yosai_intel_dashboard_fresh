"""Example demonstrating shared DatabaseConnectionFactory usage.

Multiple services obtain connections from the same factory which wraps a
:class:`DatabaseConnectionPool`. The pool is global to the factory, so
connections released by one service become immediately available to others,
allowing cross-service connection reuse.

Both synchronous and asynchronous patterns are shown below.
"""

import asyncio
from yosai_intel_dashboard.src.database.connection import create_database_connection
from yosai_intel_dashboard.src.infrastructure.config.connection_pool import (
    DatabaseConnectionPool,
)


class DatabaseConnectionFactory:
    """Factory exposing a shared connection pool."""

    def __init__(self) -> None:
        self.pool = DatabaseConnectionPool(
            factory=create_database_connection,
            initial_size=1,
            max_size=4,
            timeout=5,
            shrink_timeout=30,
        )

    def get_connection(self):
        """Retrieve a connection synchronously."""
        return self.pool.get_connection()

    def release_connection(self, conn) -> None:
        """Return a connection to the pool."""
        self.pool.release_connection(conn)

    async def get_connection_async(self):
        """Retrieve a connection inside async code."""
        return await asyncio.to_thread(self.get_connection)

    async def release_connection_async(self, conn) -> None:
        """Release a connection inside async code."""
        await asyncio.to_thread(self.release_connection, conn)


# --- Example services ---------------------------------------------------

class MetricsService:
    def __init__(self, factory: DatabaseConnectionFactory) -> None:
        self.factory = factory

    def fetch_metrics(self):
        conn = self.factory.get_connection()
        try:
            return conn.execute_query("SELECT * FROM metrics")
        finally:
            self.factory.release_connection(conn)


class AuditService:
    def __init__(self, factory: DatabaseConnectionFactory) -> None:
        self.factory = factory

    async def log_event(self, event: str) -> None:
        conn = await self.factory.get_connection_async()
        try:
            await asyncio.to_thread(
                conn.execute_command,
                "INSERT INTO audit(event) VALUES (%s)",
                (event,),
            )
        finally:
            await self.factory.release_connection_async(conn)


async def main() -> None:
    factory = DatabaseConnectionFactory()
    metrics_service = MetricsService(factory)
    audit_service = AuditService(factory)

    # Synchronous usage
    metrics_service.fetch_metrics()

    # Asynchronous usage
    await asyncio.gather(
        audit_service.log_event("login"),
        audit_service.log_event("logout"),
    )
    # Pool connections are shared across services; releasing a connection in one
    # service immediately returns it to the pool for others.


if __name__ == "__main__":
    asyncio.run(main())
