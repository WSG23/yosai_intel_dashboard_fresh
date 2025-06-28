from __future__ import annotations

"""Custom JSON provider using JsonSerializationService."""

import json
from typing import Any

from flask import Flask
from flask.json.provider import DefaultJSONProvider

from .json_serialization_plugin import JsonSerializationService


class LazyStringSafeJSONProvider(DefaultJSONProvider):
    """JSON provider that delegates serialization to JsonSerializationService."""

    def __init__(self, app: Flask, service: JsonSerializationService) -> None:
        super().__init__(app)
        self.service = service

    def dumps(self, obj: Any, **kwargs: Any) -> str:
        return self.service.serialize(obj)

    def loads(self, s: str | bytes, **kwargs: Any) -> Any:
        return json.loads(s)
