# config/cache_config.py
import os
from dataclasses import dataclass, field
from typing import Optional

from core.exceptions import ConfigurationError


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

    def __post_init__(self) -> None:
        if self.ttl <= 0 or self.jwks_ttl <= 0:
            raise ConfigurationError("Cache TTL values must be positive")
