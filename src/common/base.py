from __future__ import annotations

"""Base classes used across demo components."""

from .config import ConfigProvider, ConfigService


class BaseComponent:
    """Base class that provides access to the application configuration."""

    def __init__(self, config: ConfigProvider | None = None) -> None:
        # If no config supplied use defaults loaded from the environment.
        self._config: ConfigProvider = config or ConfigService()

    @property
    def config(self) -> ConfigProvider:
        """Configuration accessor for subclasses."""
        return self._config


__all__ = ["BaseComponent"]

