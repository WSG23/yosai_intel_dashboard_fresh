from __future__ import annotations

import importlib
import json
import time
from abc import ABC, abstractmethod
from collections import OrderedDict
from typing import Any, Dict, Tuple

import pandas as pd
import yaml

from core.performance import MetricType, get_performance_monitor


class MappingModel(ABC):
    """Abstract base class for column mapping models."""

    CACHE_SIZE = 128

    def __init__(self) -> None:
        self._cache: "OrderedDict[Tuple[str, str], Dict[str, Dict[str, Any]]]" = (
            OrderedDict()
        )
        self.monitor = get_performance_monitor()

    # ------------------------------------------------------------------
    @abstractmethod
    def suggest(self, df: pd.DataFrame, filename: str) -> Dict[str, Dict[str, Any]]:
        """Return suggested mappings for ``df``."""
        raise NotImplementedError

    # ------------------------------------------------------------------
    def cached_suggest(
        self, df: pd.DataFrame, filename: str
    ) -> Dict[str, Dict[str, Any]]:
        """Return suggestions using an internal LRU cache."""
        key = ("|".join(df.columns), filename)
        if key in self._cache:
            self._cache.move_to_end(key)
            return self._cache[key]

        start = time.time()
        result = self.suggest(df, filename)
        duration = time.time() - start
        self.monitor.record_metric(
            "mapping.suggest.latency", duration, MetricType.FILE_PROCESSING
        )
        accuracy = 0.0
        if df.columns.size:
            accuracy = sum(1 for v in result.values() if v.get("field")) / len(
                df.columns
            )
        self.monitor.record_metric(
            "mapping.suggest.accuracy", accuracy, MetricType.FILE_PROCESSING
        )
        if len(self._cache) >= self.CACHE_SIZE:
            self._cache.popitem(last=False)
        self._cache[key] = result
        return result

    # ------------------------------------------------------------------
    @classmethod
    def load_from_config(cls, path: str) -> "MappingModel":
        """Instantiate a model described by a YAML or JSON config file."""
        with open(path, "r", encoding="utf-8") as fh:
            if path.endswith((".yml", ".yaml")):
                config = yaml.safe_load(fh) or {}
            else:
                config = json.load(fh)
        model_cls = config.get("class")
        if model_cls:
            module, name = model_cls.rsplit(".", 1)
            klass = getattr(importlib.import_module(module), name)
        else:
            from . import get_registered_model

            model_type = config.get("type")
            klass = get_registered_model(model_type)
        params = config.get("params", {})
        return klass(**params)
