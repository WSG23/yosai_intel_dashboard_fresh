"""Async background workers for analytics tasks."""

from __future__ import annotations

import asyncio
import logging
from typing import Awaitable, Callable, Optional

from yosai_intel_dashboard.src.core.advanced_cache import AdvancedCacheManager, create_advanced_cache_manager

# Optional async queue integrations
try:
    import aio_pika  # type: ignore
except Exception:  # pragma: no cover - optional dependency may be missing
    aio_pika = None

try:
    import aiorq  # type: ignore
except Exception:  # pragma: no cover - optional dependency may be missing
    aiorq = None

logger = logging.getLogger(__name__)


# Default intervals in seconds
_CACHE_REFRESH_INTERVAL = 300
_CALCULATION_INTERVAL = 60

_cache_manager: AdvancedCacheManager | None = None
_cache_task: asyncio.Task | None = None
_calc_task: asyncio.Task | None = None
_queue_task: asyncio.Task | None = None
_stop_event = asyncio.Event()


async def _periodic_runner(func: Callable[[], Awaitable[None]], interval: int) -> None:
    """Run ``func`` every ``interval`` seconds until cancelled."""
    while not _stop_event.is_set():
        try:
            await func()
        except asyncio.CancelledError:
            break
        except Exception as exc:  # pragma: no cover - runtime failures
            logger.exception("Worker task failed: %s", exc)
        try:
            await asyncio.wait_for(_stop_event.wait(), interval)
        except asyncio.TimeoutError:
            continue
        except asyncio.CancelledError:
            break


async def _refresh_cache() -> None:
    """Refresh Redis or in-memory cache."""
    if _cache_manager is None:
        return
    try:
        await _cache_manager.clear()
        logger.debug("Cache refreshed")
    except Exception as exc:  # pragma: no cover - best effort
        logger.error("Cache refresh error: %s", exc, exc_info=True)


async def _perform_calculations() -> None:
    """Placeholder for periodic analytics calculations."""
    logger.debug("Running scheduled calculations")
    try:
        await asyncio.sleep(0)  # replace with real calculations
    except Exception as exc:  # pragma: no cover - best effort
        logger.error("Calculation error: %s", exc, exc_info=True)


async def _queue_worker(queue: asyncio.Queue[Awaitable[None]]) -> None:
    """Consume and execute tasks from ``queue``."""
    while not _stop_event.is_set():
        try:
            coro = await queue.get()
        except asyncio.CancelledError:
            break
        try:
            await coro
        except Exception as exc:  # pragma: no cover - best effort
            logger.exception("Queued task failed: %s", exc)
        finally:
            queue.task_done()


async def start_workers(
    *,
    calc_interval: int = _CALCULATION_INTERVAL,
    cache_refresh_interval: int = _CACHE_REFRESH_INTERVAL,
    task_queue: Optional[asyncio.Queue[Awaitable[None]]] = None,
) -> None:
    """Start background workers."""
    global _cache_manager, _calc_task, _cache_task, _queue_task

    if _calc_task or _cache_task:
        return

    _stop_event.clear()
    _cache_manager = await create_advanced_cache_manager()
    _calc_task = asyncio.create_task(
        _periodic_runner(_perform_calculations, calc_interval)
    )
    _cache_task = asyncio.create_task(
        _periodic_runner(_refresh_cache, cache_refresh_interval)
    )
    if task_queue is not None:
        _queue_task = asyncio.create_task(_queue_worker(task_queue))
    logger.info("Analytics workers started")


async def stop_workers() -> None:
    """Stop all running workers and cleanup resources."""
    global _cache_manager, _calc_task, _cache_task, _queue_task

    _stop_event.set()

    for task in (_calc_task, _cache_task, _queue_task):
        if task is not None:
            task.cancel()
            try:
                await task
            except asyncio.CancelledError:
                pass
    _calc_task = _cache_task = _queue_task = None

    if _cache_manager is not None:
        await _cache_manager.stop()
        _cache_manager = None

    logger.info("Analytics workers stopped")


__all__ = ["start_workers", "stop_workers"]
