import asyncio
import os
from datetime import datetime

import asyncpg


async def verify_migration_status() -> bool:
    """Verify TimescaleDB migration completeness."""
    conn = await asyncpg.connect(
        host=os.getenv("TIMESCALE_HOST", "localhost"),
        port=int(os.getenv("TIMESCALE_PORT", "5433")),
        database=os.getenv("TIMESCALE_DB_NAME", "yosai_intel"),
        user=os.getenv("TIMESCALE_DB_USER", "postgres"),
        password=os.getenv("TIMESCALE_DB_PASSWORD"),
    )

    try:
        hypertables = await conn.fetch(
            """
            SELECT hypertable_name, compression_enabled
            FROM timescaledb_information.hypertables
            """
        )

        event_count = await conn.fetchval("SELECT COUNT(*) FROM access_events")

        start = datetime.now()
        await conn.fetch(
            """
            SELECT time_bucket('1 hour', event_timestamp) AS bucket,
                   COUNT(*) AS event_count
            FROM access_events
            WHERE event_timestamp > NOW() - INTERVAL '7 days'
            GROUP BY bucket
            ORDER BY bucket DESC
            """
        )
        query_time = (datetime.now() - start).total_seconds()

        print(f"\u2713 Hypertables: {len(hypertables)}")
        print(f"\u2713 Events migrated: {event_count:,}")
        print(f"\u2713 Query performance: {query_time:.3f}s")
        return event_count > 0 and query_time < 0.1
    finally:
        await conn.close()


if __name__ == "__main__":
    success = asyncio.run(verify_migration_status())
    if not success:
        raise SystemExit("Migration verification failed")
