from __future__ import annotations

import json
import random
from datetime import datetime
from pathlib import Path
from typing import Any, Callable, Dict, Tuple


class ModelService:
    """Serve models based on versioned metadata stored in ``registry.json``."""

    def __init__(self, registry_path: Path | None = None) -> None:
        self.registry_path = registry_path or Path("models/registry.json")
        self._registry: Dict[str, Any] = {}
        self._models: Dict[str, Dict[str, Callable[[float], float]]] = {}
        self._load_registry()

    def _load_registry(self) -> None:
        if self.registry_path.exists():
            with open(self.registry_path, "r", encoding="utf-8") as fh:
                self._registry = json.load(fh)
        else:
            self._registry = {}
        for name, meta in self._registry.items():
            versions = meta.get("versions", {})
            self._models.setdefault(name, {})
            for ver, info in versions.items():
                factor = float(info.get("factor", ver))
                # Store simple lambda as placeholder model
                self._models[name][ver] = lambda x, factor=factor: x * factor

    def register_model(self, name: str, version: str, metadata: Dict[str, Any]) -> None:
        meta = self._registry.setdefault(
            name, {"versions": {}, "active": version, "rollout": {}}
        )
        entry = dict(metadata)
        entry.setdefault("timestamp", datetime.utcnow().isoformat())
        meta["versions"][version] = entry
        meta["rollout"].setdefault(version, 1.0)
        self._save()
        self._load_registry()

    def _save(self) -> None:
        self.registry_path.parent.mkdir(parents=True, exist_ok=True)
        with open(self.registry_path, "w", encoding="utf-8") as fh:
            json.dump(self._registry, fh, indent=2)

    def set_rollout(self, name: str, rollout: Dict[str, float]) -> None:
        if name not in self._registry:
            raise KeyError(f"Unknown model {name}")
        total = sum(rollout.values()) or 1.0
        normalized = {k: v / total for k, v in rollout.items()}
        self._registry[name]["rollout"] = normalized
        self._registry[name]["active"] = max(normalized, key=normalized.get)
        self._save()

    def _select_version(self, name: str) -> str:
        meta = self._registry[name]
        rollout = meta.get("rollout", {})
        if not rollout:
            return meta.get("active")
        rand = random.random()
        cumulative = 0.0
        for ver, weight in rollout.items():
            cumulative += weight
            if rand < cumulative:
                return ver
        return meta.get("active")

    def get_model(self, name: str, version: str | None = None) -> Tuple[Callable[[float], float], str]:
        if name not in self._models:
            raise KeyError(f"Unknown model {name}")
        ver = version or self._select_version(name)
        model = self._models[name][ver]
        return model, ver

    def metadata(self, name: str) -> Dict[str, Any]:
        return self._registry.get(name, {})

    def list_models(self) -> Dict[str, Any]:
        return self._registry
