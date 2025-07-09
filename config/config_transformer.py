from typing import Any


class ConfigTransformer:
    """Optional hook to transform the final Config object."""

    def transform(self, config: Any) -> Any:
        """Return transformed configuration."""
        return config
