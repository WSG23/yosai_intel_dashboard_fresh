# Cache Key Reference

This document maps cache key patterns to their owning components and describes how entries are
expired or invalidated.

| Key Pattern | Description | Owner | TTL / Invalidation |
|-------------|-------------|-------|--------------------|
| `token:<tokenID>` | JWT claims cached by the gateway | Gateway Auth Service | TTL set per token, removable via `Delete` |
| `blacklist:<tokenID>` | Blacklisted JWT tokens | Gateway Auth Service | TTL on blacklist entry, checked on access |
| `decision:<personID>:<doorID>` | Access control decisions | Gateway Rule Engine | TTL from `CACHE_TTL_SECONDS` or `InvalidateDecision` |
| `cache:<path>:<hash>` | API response cache entries | Gateway API Cache Plugin | TTL per cache rule and path invalidation |
| `yosai:<key>` | Application/service level data | Service Cache Manager | Configurable TTL or explicit delete |

Each cache entry should be invalidated explicitly or allowed to expire based on these TTL settings.
