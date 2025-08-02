# config/cache_config.py
from __future__ import annotations

import os
from dataclasses import dataclass, field
from typing import List, Optional

from yosai_intel_dashboard.src.core.exceptions import ConfigurationError


@dataclass
class CacheConfig:
    """Configuration for caching system"""

    enabled: bool = True
    ttl: int = field(default_factory=lambda: int(os.getenv("CACHE_TTL_SECONDS", "300")))
    jwks_ttl: int = field(
        default_factory=lambda: int(os.getenv("JWKS_CACHE_TTL", "300"))
    )
    max_size: int = 1000
    redis_url: Optional[str] = None
    use_memory_cache: bool = True
    use_redis: bool = False
    prefix: str = "yosai_"
    warm_keys: List[str] = field(
        default_factory=lambda: [
            k.strip() for k in os.getenv("CACHE_WARM_KEYS", "").split(",") if k.strip()
        ]
    )

    def __post_init__(self) -> None:
        if self.ttl <= 0 or self.jwks_ttl <= 0:
            raise ConfigurationError("Cache TTL values must be positive")
