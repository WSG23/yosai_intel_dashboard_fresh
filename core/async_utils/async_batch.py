from __future__ import annotations

from collections.abc import AsyncIterable, Iterable
from typing import AsyncIterator, List, TypeVar

T = TypeVar("T")


async def async_batch(
    source: AsyncIterable[T] | Iterable[T], size: int
) -> AsyncIterator[List[T]]:
    """Yield lists of ``size`` items from ``source``.

    ``source`` can be an async iterable or regular iterable. Remaining
    items smaller than ``size`` are yielded at the end.
    """

    batch: List[T] = []
    if isinstance(source, AsyncIterable):
        async for item in source:
            batch.append(item)
            if len(batch) >= size:
                yield batch
                batch = []
    else:
        for item in source:
            batch.append(item)
            if len(batch) >= size:
                yield batch
                batch = []
    if batch:
        yield batch
