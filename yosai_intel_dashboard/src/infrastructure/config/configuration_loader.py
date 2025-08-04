from __future__ import annotations

from typing import Any

from .dynamic_config import dynamic_config


class ConfigurationLoader:
    """Provide access to configuration sections for services."""

    @staticmethod
    def get_service_config(name: str) -> Any:
        """Return configuration section for the given service name.

        Parameters
        ----------
        name:
            Name of the configuration section. For example ``"security"``.

        Returns
        -------
        Any
            The configuration object for the requested service.

        Raises
        ------
        KeyError
            If the requested configuration section does not exist.
        """

        try:
            return getattr(dynamic_config, name)
        except AttributeError as exc:  # pragma: no cover - defensive
            raise KeyError(f"Unknown service configuration: {name}") from exc
