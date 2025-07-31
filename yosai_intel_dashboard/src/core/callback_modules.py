from __future__ import annotations

"""Modular callback module registry."""

import logging
from abc import abstractmethod
from typing import TYPE_CHECKING, Any, Dict, List, Optional, Protocol, runtime_checkable

from .base_model import BaseModel

if TYPE_CHECKING:  # pragma: no cover
    from .truly_unified_callbacks import TrulyUnifiedCallbacks

logger = logging.getLogger(__name__)


@runtime_checkable
class CallbackModule(Protocol):
    """Protocol for modular callback components."""

    COMPONENT_ID: str
    NAMESPACE: str

    @abstractmethod
    def register_callbacks(self, manager: "TrulyUnifiedCallbacks") -> None:
        """Register all callbacks for this module."""

    @abstractmethod
    def get_callback_ids(self) -> List[str]:
        """Return list of callback IDs this module registers."""


class CallbackModuleRegistry(BaseModel):
    """Central registry for callback modules."""

    def __init__(
        self,
        config: Optional[Any] = None,
        db: Optional[Any] = None,
        logger: Optional[logging.Logger] = None,
    ) -> None:
        super().__init__(config, db, logger)
        self._modules: Dict[str, CallbackModule] = {}
        self._registered_ids: set[str] = set()

    # ------------------------------------------------------------------
    def register_module(self, module: CallbackModule) -> bool:
        """Register a callback module, checking for conflicts."""
        module_id = module.COMPONENT_ID

        if module_id in self._modules:
            logger.warning(f"Module {module_id} already registered")
            return False

        callback_ids = module.get_callback_ids()
        conflicts = [cid for cid in callback_ids if cid in self._registered_ids]
        if conflicts:
            logger.error(f"Module {module_id} has conflicting callbacks: {conflicts}")
            return False

        self._modules[module_id] = module
        self._registered_ids.update(callback_ids)

        return True

    # ------------------------------------------------------------------
    def get_module(self, module_id: str) -> CallbackModule | None:
        """Get a registered module by ID."""
        return self._modules.get(module_id)

    # ------------------------------------------------------------------
    def initialize_all(self, manager: "TrulyUnifiedCallbacks") -> None:
        """Initialize all registered modules with the callback manager."""
        for module_id, module in self._modules.items():
            try:
                module.register_callbacks(manager)
                logger.info(f"Initialized module: {module_id}")
            except Exception as exc:  # pragma: no cover - defensive
                logger.error(f"Failed to initialize {module_id}: {exc}")


__all__ = ["CallbackModule", "CallbackModuleRegistry"]
