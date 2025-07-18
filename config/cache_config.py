# config/cache_config.py
from dataclasses import dataclass
from typing import Optional

@dataclass
class CacheConfig:
    """Configuration for caching system"""
    enabled: bool = True
    ttl: int = 3600  # Time to live in seconds
    max_size: int = 1000
    redis_url: Optional[str] = None
    use_memory_cache: bool = True
    use_redis: bool = False
    prefix: str = "yosai_"
