"""Backward compatibility wrapper for ``ClientSideValidator``."""

from __future__ import annotations

import warnings

from .validator import ClientSideValidator as _ClientSideValidator


class ClientSideValidator(_ClientSideValidator):
    """Deprecated alias for :class:`validator.ClientSideValidator`."""

    def __init__(self, *args, **kwargs) -> None:  # type: ignore[override]
        warnings.warn(
            "services.upload.validators.ClientSideValidator is deprecated; "
            "use services.upload.validator.ClientSideValidator",
            DeprecationWarning,
            stacklevel=2,
        )
        super().__init__(*args, **kwargs)


__all__ = ["ClientSideValidator"]

