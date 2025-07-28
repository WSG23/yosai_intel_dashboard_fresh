"""
Centralized Callback Registry for Dash Application
Manages all callbacks in a modular, organized way
"""

import functools
import logging
import time
from functools import wraps
from typing import TYPE_CHECKING, Any, Callable, Dict, Iterable, List, Optional

from dash import no_update

if TYPE_CHECKING:  # pragma: no cover - avoid circular import at runtime
    from .truly_unified_callbacks import TrulyUnifiedCallbacks

from .base_model import BaseModel


def debounce(wait_ms: int = 300):
    """Return decorator to suppress rapid callback invocations."""

    def decorator(func: Callable):
        last_call = 0.0

        @wraps(func)
        def wrapper(*args, **kwargs):
            nonlocal last_call
            now = time.monotonic() * 1000
            if now - last_call < wait_ms:
                return no_update
            last_call = now
            return func(*args, **kwargs)

        return wrapper

    return decorator


logger = logging.getLogger(__name__)


class GlobalCallbackRegistry(BaseModel):
    """Track globally registered callback IDs to prevent duplicates."""

    def __init__(
        self,
        config: Optional[Any] = None,
        db: Optional[Any] = None,
        logger: Optional[logging.Logger] = None,
    ) -> None:
        super().__init__(config, db, logger)
        self.registered_callbacks: set[str] = set()
        self.registration_sources: Dict[str, str] = {}
        self.callback_sources = self.registration_sources  # backward compatibility
        self.registration_attempts: Dict[str, int] = {}
        self.registration_order: List[str] = []

    def is_registered(self, callback_id: str) -> bool:
        return callback_id in self.registered_callbacks

    def register(self, callback_id: str, module_name: str = "unknown") -> bool:
        self.registration_attempts[callback_id] = (
            self.registration_attempts.get(callback_id, 0) + 1
        )
        if callback_id in self.registered_callbacks:
            existing = self.callback_sources.get(callback_id, "unknown")
            logger.warning(
                f"Callback ID '{callback_id}' already registered by {existing}, "
                f"skipping registration from {module_name}"
            )
            return False

        self.registered_callbacks.add(callback_id)
        self.registration_sources[callback_id] = module_name
        self.registration_order.append(callback_id)
        logger.debug(f"Registered callback '{callback_id}' from {module_name}")
        return True

    def get_conflicts(self) -> Dict[str, str]:
        return dict(self.registration_sources)

    def register_deduplicated(
        self,
        callback_ids: Iterable[str],
        register_func: Callable[[], Any],
        *,
        source_module: str = "unknown",
    ) -> bool:
        """Register callbacks if none of ``callback_ids`` are already registered."""

        duplicates = [cid for cid in callback_ids if cid in self.registered_callbacks]
        if duplicates:
            existing = {
                cid: self.callback_sources.get(cid, "unknown") for cid in duplicates
            }
            logger.info(
                f"Skipping duplicate callback registration from {source_module}: {existing}"
            )
            return False

        try:
            register_func()
        except Exception as exc:  # pragma: no cover - defensive
            logger.error(
                f"Failed to register callbacks {list(callback_ids)} from {source_module}: {exc}"
            )
            return False

        for cid in callback_ids:
            self.register(cid, source_module)
        return True

    def validate_registration_integrity(self) -> bool:
        """Return True if all registrations are unique and tracked."""

        duplicates = {
            cid: count for cid, count in self.registration_attempts.items() if count > 1
        }
        missing = [
            cid
            for cid in self.registered_callbacks
            if cid not in self.registration_sources
        ]
        return not duplicates and not missing


# Global instance used across the application
_callback_registry = GlobalCallbackRegistry()


class CallbackRegistry:
    """Central registry for all application callbacks"""

    def __init__(self, callbacks: "TrulyUnifiedCallbacks") -> None:
        """Initialize with a :class:`TrulyUnifiedCallbacks` instance."""
        self.callbacks = callbacks
        self.app = callbacks.app
        self.registered_callbacks: Dict[str, Any] = {}
        self.clientside_callbacks: Dict[str, Any] = {}

    # New unified decorator -----------------------------------------------
    def handle_unified(self, *args, **kwargs):
        """Return :class:`CallbackUnifier` bound to this registry."""
        from .plugins.callback_unifier import CallbackUnifier
        from .plugins.decorators import safe_callback

        return CallbackUnifier(self, safe_callback(self.app))(*args, **kwargs)

    def handle_register(
        self,
        outputs,
        inputs: List,
        states: List = None,
        prevent_initial_call: bool = True,
        callback_id: str = None,
        allow_duplicate: bool = False,
    ):
        """Decorator to register callbacks"""

        def decorator(func: Callable):
            if callback_id and callback_id in self.registered_callbacks:
                logger.warning(f"Callback {callback_id} already registered, skipping")
                return func

            try:
                # Handle allow_duplicate for Output objects
                if allow_duplicate and hasattr(outputs, "__iter__"):
                    for output in outputs if isinstance(outputs, list) else [outputs]:
                        if hasattr(output, "allow_duplicate"):
                            output.allow_duplicate = True

                wrapper = self.callbacks.handle_register(
                    outputs,
                    inputs,
                    states,
                    callback_id=callback_id or func.__name__,
                    component_name="callback_registry",
                    prevent_initial_call=prevent_initial_call,
                    allow_duplicate=allow_duplicate,
                )(func)

                if callback_id:
                    self.registered_callbacks[callback_id] = wrapper
                    logger.debug(f"Registered callback: {callback_id}")

                return wrapper
            except Exception as e:
                logger.error(f"Failed to register callback {callback_id}: {e}")
                return func

        return decorator

    def handle_register_clientside(
        self,
        clientside_function: str,
        outputs,  # Don't specify type - can be single or list
        inputs: List,
        states: List = None,
        callback_id: str = None,
    ):
        """Register clientside callbacks"""
        if callback_id and callback_id in self.clientside_callbacks:
            logger.warning(
                f"Clientside callback {callback_id} already registered, skipping"
            )
            return

        try:
            self.app.clientside_callback(
                clientside_function, outputs, inputs, states or []  # Pass as-is
            )

            if callback_id:
                self.clientside_callbacks[callback_id] = True
                logger.debug(f"Registered clientside callback: {callback_id}")

        except Exception as e:
            logger.error(f"Failed to register clientside callback {callback_id}: {e}")


class ComponentCallbackManager:
    """Base class for component callback managers"""

    def __init__(self, callback_registry: CallbackRegistry):
        self.registry = callback_registry
        self.component_name = self.__class__.__name__.replace("CallbackManager", "")

    def register_all(self):
        """Register all callbacks for this component"""
        raise NotImplementedError("Subclasses must implement register_all")


def safe_callback_registration(callback_id: str, module_name: str = "unknown"):
    """Decorator to prevent duplicate callback registrations."""

    def decorator(register_func: Callable):
        @functools.wraps(register_func)
        def wrapper(*args, **kwargs):
            if _callback_registry.is_registered(callback_id):
                logger.info(f"Skipping duplicate callback registration: {callback_id}")
                return None
            result = register_func(*args, **kwargs)
            _callback_registry.register(callback_id, module_name)
            return result

        return wrapper

    return decorator


def handle_register_with_deduplication(
    manager: "TrulyUnifiedCallbacks",
    outputs: Any,
    inputs: List | Any | None = None,
    states: List | Any | None = None,
    *,
    callback_id: str,
    component_name: str,
    source_module: str = "unknown",
    allow_duplicate: bool = False,
    **kwargs: Any,
) -> Callable[[Callable[..., Any]], Callable[..., Any]]:
    """Register callback if not already registered using the global registry."""

    _callback_registry.registration_attempts[callback_id] = (
        _callback_registry.registration_attempts.get(callback_id, 0) + 1
    )

    if _callback_registry.is_registered(callback_id):
        logger.info(
            f"Skipping duplicate callback registration: {callback_id} from {source_module}"
        )
        return lambda func: func

    decorator = manager.handle_register(
        outputs,
        inputs=inputs,
        states=states,
        callback_id=callback_id,
        component_name=component_name,
        allow_duplicate=allow_duplicate,
        **kwargs,
    )

    def wrapper(func: Callable[..., Any]) -> Callable[..., Any]:
        registered = decorator(func)
        _callback_registry.register(callback_id, source_module)
        return registered

    return wrapper


def get_registration_diagnostics() -> Dict[str, Any]:
    """Return diagnostic information about callback registrations."""

    return {
        "attempts": dict(_callback_registry.registration_attempts),
        "sources": dict(_callback_registry.registration_sources),
        "order": list(_callback_registry.registration_order),
    }


def validate_registration_integrity() -> bool:
    """Return True if all registrations are unique and tracked."""

    return _callback_registry.validate_registration_integrity()


__all__ = [
    "CallbackRegistry",
    "ComponentCallbackManager",
    "GlobalCallbackRegistry",
    "safe_callback_registration",
    "handle_register_with_deduplication",
    "get_registration_diagnostics",
    "validate_registration_integrity",
    "_callback_registry",
]
