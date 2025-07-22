from __future__ import annotations

"""Modular callback module registry."""

import logging
from abc import abstractmethod
from typing import TYPE_CHECKING, Dict, List, Protocol, runtime_checkable

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


class CallbackModuleRegistry:
    """Central registry for callback modules."""

    def __init__(self) -> None:
        self._modules: Dict[str, CallbackModule] = {}
        self._callback_map: Dict[str, str] = {}

    # ------------------------------------------------------------------
    def register_module(self, module: CallbackModule) -> bool:
        """Register a callback module, checking for conflicts."""
        module_id = module.COMPONENT_ID

        if module_id in self._modules:
            logger.warning("Module %s already registered", module_id)
            return False

        callback_ids = module.get_callback_ids()
        conflicts = [cid for cid in callback_ids if cid in self._callback_map]
        if conflicts:
            logger.error(
                "Module %s has conflicting callbacks: %s", module_id, conflicts
            )
            return False

        self._modules[module_id] = module
        for cid in callback_ids:
            self._callback_map[cid] = module_id

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
                logger.info("Initialized module: %s", module_id)
            except Exception as exc:  # pragma: no cover - defensive
                logger.error("Failed to initialize %s: %s", module_id, exc)


__all__ = ["CallbackModule", "CallbackModuleRegistry"]
