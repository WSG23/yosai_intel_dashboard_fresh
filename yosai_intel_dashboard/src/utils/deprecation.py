from __future__ import annotations

import logging
import warnings
from functools import lru_cache
from pathlib import Path
from typing import Any, Dict

try:  # pragma: no cover - optional metrics dependency
    from metrics import increment  # type: ignore
except Exception:  # pragma: no cover - gracefully handle missing metrics

    def increment(*args: Any, **kwargs: Any) -> None:
        """Fallback increment when metrics library is unavailable."""
        return None


logger = logging.getLogger(__name__)


@lru_cache(maxsize=None)
def _load_config() -> Dict[str, Dict[str, str]]:
    """Return deprecation configuration indexed by component."""
    root = Path(__file__).resolve().parents[3]
    config_path = root / "deprecation.yml"
    if not config_path.exists():
        return {}
    import yaml  # imported lazily to avoid dependency if unused

    with config_path.open("r", encoding="utf-8") as fh:
        data = yaml.safe_load(fh) or []
    return {item.get("component"): item for item in data if isinstance(item, dict)}


def warn(component: str) -> None:
    """Emit a standardized deprecation warning for ``component``.

    The warning is visible by default, logged, and a usage metric is emitted.
    """
    info = _load_config().get(component, {})
    since = info.get("deprecated_since")
    removal = info.get("removal_version")
    migration = info.get("migration_path")

    message_parts = [f"{component} is deprecated"]
    if since:
        message_parts.append(f" since {since}")
    if removal:
        message_parts.append(f" and will be removed in {removal}")
    if migration:
        message_parts.append(f". See {migration} for migration guidance.")

    message = "".join(message_parts)
    warnings.warn(message, DeprecationWarning, stacklevel=2)
    logger.warning(message)
    try:
        increment("deprecation.usage", tags={"component": component})
    except Exception:  # pragma: no cover - defensive
        logger.debug("Failed to emit deprecation metric", exc_info=True)


__all__ = ["warn"]
