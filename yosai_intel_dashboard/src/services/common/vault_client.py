from __future__ import annotations

import logging
import time
from typing import Any, Dict, Optional

from optional_dependencies import import_optional

hvac = import_optional("hvac")


class VaultClient:
    """Simple wrapper around :class:`hvac.Client` with caching and retries."""

    log = logging.getLogger(__name__)

    def __init__(self, url: str, token: str, *, max_attempts: int = 3) -> None:
        if not hvac:
            raise RuntimeError("hvac is required for VaultClient")
        self.client = hvac.Client(url=url, token=token)
        self.max_attempts = max_attempts
        self._cache: Dict[str, Any] = {}

    # ------------------------------------------------------------------
    def _read_secret(self, path: str) -> Dict[str, Any]:
        attempt = 1
        delay = 0.5
        while True:
            try:
                secret = self.client.secrets.kv.v2.read_secret_version(path=path)
                return secret["data"]["data"]
            except Exception as exc:  # pragma: no cover - network error
                if attempt >= self.max_attempts:
                    raise
                self.log.warning("vault read failed: %s", exc)
                time.sleep(delay)
                delay *= 2
                attempt += 1

    # ------------------------------------------------------------------
    def get_secret(self, path: str, field: Optional[str] = None) -> Optional[Any]:
        key = f"{path}#{field}" if field else path
        if key in self._cache:
            return self._cache[key]
        self.log.info("read secret %s", key)
        data = self._read_secret(path)
        value = data.get(field) if field else data
        self._cache[key] = value
        return value

    # ------------------------------------------------------------------
    def invalidate(self, key: Optional[str] = None) -> None:
        if key is None:
            self._cache.clear()
        else:
            self._cache.pop(key, None)


__all__ = ["VaultClient"]
