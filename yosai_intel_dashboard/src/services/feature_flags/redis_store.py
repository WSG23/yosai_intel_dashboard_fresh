import asyncio
import logging
import threading
from contextlib import contextmanager
from typing import Dict

import redis.asyncio as redis

logger = logging.getLogger(__name__)


class ReadWriteLock:
    """A simple reader-writer lock."""

    def __init__(self) -> None:
        self._cond = threading.Condition()
        self._readers = 0

    @contextmanager
    def read_lock(self):
        with self._cond:
            self._readers += 1
        try:
            yield
        finally:
            with self._cond:
                self._readers -= 1
                if self._readers == 0:
                    self._cond.notify_all()

    @contextmanager
    def write_lock(self):
        with self._cond:
            while self._readers > 0:
                self._cond.wait()
            self._readers = -1
        try:
            yield
        finally:
            with self._cond:
                self._readers = 0
                self._cond.notify_all()


class RedisFeatureFlagStore:
    """Persist feature flags in Redis with a local in-memory cache."""

    def __init__(
        self,
        redis_url: str = "redis://localhost:6379/0",
        prefix: str = "feature_flag:",
        channel: str = "feature_flags:updates",
    ) -> None:
        self.redis_url = redis_url
        self.prefix = prefix
        self.channel = channel
        self._redis: redis.Redis = redis.from_url(redis_url, decode_responses=True)
        self._flags: Dict[str, bool] = {}
        self._lock = ReadWriteLock()
        self._pubsub_thread: threading.Thread | None = None
        self._stop = threading.Event()

    def _key(self, name: str) -> str:
        return f"{self.prefix}{name}"

    async def _load_all(self) -> None:
        keys = await self._redis.keys(f"{self.prefix}*")
        data: Dict[str, bool] = {}
        for key in keys:
            name = key[len(self.prefix) :]
            val = await self._redis.hget(key, "enabled")
            data[name] = bool(int(val)) if val is not None else False
        with self._lock.write_lock():
            self._flags = data

    def start(self) -> None:
        """Start Pub/Sub listener and warm the cache."""
        if self._pubsub_thread and self._pubsub_thread.is_alive():
            return
        asyncio.run(self._load_all())
        self._stop.clear()
        self._pubsub_thread = threading.Thread(target=self._run_listener, daemon=True)
        self._pubsub_thread.start()

    def stop(self) -> None:
        """Stop the Pub/Sub listener."""
        if self._pubsub_thread:
            self._stop.set()
            self._pubsub_thread.join()
            self._pubsub_thread = None
        asyncio.run(self._redis.close())

    def _run_listener(self) -> None:
        asyncio.run(self._listener())

    async def _listener(self) -> None:
        pubsub = self._redis.pubsub()
        await pubsub.subscribe(self.channel)
        try:
            while not self._stop.is_set():
                message = await pubsub.get_message(
                    ignore_subscribe_messages=True, timeout=1.0
                )
                if message is None:
                    continue
                name = message.get("data")
                if not isinstance(name, str):
                    continue
                val = await self._redis.hget(self._key(name), "enabled")
                if val is None:
                    continue
                flag = bool(int(val))
                with self._lock.write_lock():
                    self._flags[name] = flag
        finally:
            await asyncio.gather(
                pubsub.unsubscribe(self.channel),
                pubsub.close(),
            )

    def get_flag(self, name: str, default: bool = False) -> bool:
        with self._lock.read_lock():
            if name in self._flags:
                return self._flags[name]
        val = asyncio.run(self._redis.hget(self._key(name), "enabled"))
        if val is None:
            return default
        flag = bool(int(val))
        with self._lock.write_lock():
            self._flags[name] = flag
        return flag

    def set_flag(self, name: str, value: bool) -> None:
        asyncio.run(
            self._redis.hset(self._key(name), mapping={"enabled": int(value)})
        )
        with self._lock.write_lock():
            self._flags[name] = value
        asyncio.run(self._redis.publish(self.channel, name))

    def get_all(self) -> Dict[str, bool]:
        with self._lock.read_lock():
            return dict(self._flags)
