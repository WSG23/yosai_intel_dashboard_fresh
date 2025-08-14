# Cache Key Reference

This document maps cache key patterns to their owning components.

| Key Pattern | Description | Owner |
|-------------|-------------|-------|
| `token:<tokenID>` | JWT claims cached by the gateway | Gateway Auth Service |
| `blacklist:<tokenID>` | Blacklisted JWT tokens | Gateway Auth Service |
| `decision:<personID>:<doorID>` | Access control decisions | Gateway Rule Engine |
| `cache:<path>:<hash>` | API response cache entries | Gateway API Cache Plugin |
| `yosai:<key>` | Application/service level data | Service Cache Manager |

Each cache entry should be invalidated explicitly or allowed to expire based on TTL settings.
