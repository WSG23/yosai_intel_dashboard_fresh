from __future__ import annotations

"""Truly unified callback system combining registry and coordinator."""

import asyncio
import logging
import threading
import time
from collections import defaultdict
from dataclasses import dataclass
from typing import (
    TYPE_CHECKING,
    Any,
    Awaitable,
    Callable,
    Dict,
    Iterable,
    List,
    Optional,
    Protocol,
    Tuple,
    Type,
    TypeAlias,
    TypedDict,
)

from dash import Dash
from dash.dependencies import Input, Output, State

from .callback_registry import CallbackRegistry, ComponentCallbackManager
from .events import CallbackEvent
from ..event_bus import EventBus, EventPublisher

# ---------------------------------------------------------------------------
# Type aliases
# ---------------------------------------------------------------------------
Outputs: TypeAlias = Output | tuple[Output, ...]
Inputs: TypeAlias = Input | tuple[Input, ...] | None
States: TypeAlias = State | tuple[State, ...] | None


logger = logging.getLogger(__name__)


class CallbackHandler(Protocol):  # noqa: F811
    """Protocol for synchronous or asynchronous callback handlers."""

    def __call__(self, *args: Any, **kwargs: Any) -> Any | Awaitable[Any]: ...


@dataclass
class Operation:
    """Represent a single callback operation."""

    name: str
    func: CallbackHandler
    timeout: Optional[float] = None
    retries: int = 0


@dataclass(frozen=True)
class DashCallbackRegistration:
    """Data about a registered Dash callback."""

    callback_id: str
    component_name: str
    outputs: Tuple[Output, ...]
    inputs: Tuple[Input, ...]
    states: Tuple[State, ...]


class CallbackMetrics(TypedDict):
    """Execution metrics for a callback event."""

    calls: int
    exceptions: int
    total_time: float


if TYPE_CHECKING:  # pragma: no cover - for type hints only
    from validation.security_validator import SecurityValidator

    from ...core.plugins.callback_unifier import (  # noqa: F401
        CallbackUnifier as _CallbackUnifier,
    )


class TrulyUnifiedCallbacks(EventPublisher):
    """Unified system providing event, Dash and operation callbacks."""

    def __init__(
        self,
        app: Dash | None = None,
        *,
        security_validator: SecurityValidator | None = None,
        event_bus: EventBus | None = None,
    ) -> None:
        super().__init__(event_bus)
        self.app: Dash | None = app
        if security_validator is None:
            from validation.security_validator import SecurityValidator

            security_validator = SecurityValidator()
        self.security: SecurityValidator = security_validator
        self._lock: threading.RLock = threading.RLock()
        self._dash_callbacks: dict[str, DashCallbackRegistration] = {}
        self._output_map: dict[str, str] = {}
        self._namespaces: dict[str, list[str]] = defaultdict(list)
        self._groups: dict[str, list[Operation]] = defaultdict(list)
        self._registered_components: set[str] = set()

    # ------------------------------------------------------------------
    def callback(
        self, *args: Any, **kwargs: Any
    ) -> Callable[[CallbackHandler], CallbackHandler]:
        """Unified callback decorator for Dash callbacks."""
        from ...core.plugins.callback_unifier import CallbackUnifier

        return CallbackUnifier(self)(*args, **kwargs)

    unified_callback = callback

    # Dash callback registration ---------------------------------------
    def handle_register(
        self,
        outputs: Outputs,
        inputs: Inputs = None,
        states: States = None,
        *,
        callback_id: str,
        component_name: str,
        allow_duplicate: bool = False,
        **kwargs: Any,
    ) -> Callable[[CallbackHandler], CallbackHandler]:
        """Register a Dash callback and track conflicts.

        Thread-safe via an internal ``RLock``.
        """

        if self.app is None:
            raise RuntimeError("Dash app not configured for TrulyUnifiedCallbacks")

        if inputs is None:
            inputs_tuple: Tuple[Input, ...] = tuple()
            inputs_arg = None
        elif isinstance(inputs, (list, tuple)):
            inputs_tuple = tuple(inputs)
            inputs_arg = inputs
        else:
            inputs_tuple = (inputs,)
            inputs_arg = inputs

        if states is None:
            states_tuple: Tuple[State, ...] = tuple()
            states_arg = None
        elif isinstance(states, (list, tuple)):
            states_tuple = tuple(states)
            states_arg = states
        else:
            states_tuple = (states,)
            states_arg = states

        outputs_tuple = outputs if isinstance(outputs, (list, tuple)) else (outputs,)

        def decorator(func: CallbackHandler) -> CallbackHandler:
            with self._lock:
                if callback_id in self._dash_callbacks:
                    raise ValueError(f"Callback ID '{callback_id}' already registered")

                for o in outputs_tuple:
                    key = f"{o.component_id}.{o.component_property}"
                    allow_dup_output = allow_duplicate or getattr(
                        o, "allow_duplicate", False
                    )
                    if key in self._output_map and not allow_dup_output:
                        logger.warning(f"Output '{key}' conflict - allowing duplicate")

                from ...core.dash_callback_middleware import wrap_callback

                wrapped_callback = wrap_callback(func, outputs_tuple, self.security)
                wrapped = self.app.callback(
                    outputs,
                    inputs_arg if inputs_arg is not None else inputs_tuple,
                    states_arg if states_arg is not None else states_tuple,
                    **kwargs,
                )(wrapped_callback)

                reg = DashCallbackRegistration(
                    callback_id=callback_id,
                    component_name=component_name,
                    outputs=tuple(outputs_tuple),
                    inputs=inputs_tuple,
                    states=states_tuple,
                )
                self._dash_callbacks[callback_id] = reg
                for o in outputs_tuple:
                    key = f"{o.component_id}.{o.component_property}"
                    self._output_map.setdefault(key, callback_id)
                self._namespaces[component_name].append(callback_id)
                return wrapped

        return decorator

    # ------------------------------------------------------------------
    def register_callback(
        self,
        outputs: Outputs,
        inputs: Inputs = None,
        states: States = None,
        *,
        callback_id: str,
        component_name: str,
        allow_duplicate: bool = False,
        **kwargs: Any,
    ) -> Callable[[CallbackHandler], CallbackHandler]:
        """Alias for :meth:`handle_register`.

        Thread-safe via :meth:`handle_register`'s internal ``RLock``.
        """

        return self.handle_register(
            outputs=outputs,
            inputs=inputs,
            states=states,
            callback_id=callback_id,
            component_name=component_name,
            allow_duplicate=allow_duplicate,
            **kwargs,
        )

    # ------------------------------------------------------------------
    def register_handler(
        self,
        outputs: Outputs,
        inputs: Inputs = None,
        states: States = None,
        *,
        callback_id: str,
        component_name: str,
        allow_duplicate: bool = False,
        **kwargs: Any,
    ) -> Callable[[CallbackHandler], CallbackHandler]:
        """Alias for :meth:`handle_register`.

        Thread-safe via :meth:`handle_register`'s internal ``RLock``.
        """

        return self.handle_register(
            outputs=outputs,
            inputs=inputs,
            states=states,
            callback_id=callback_id,
            component_name=component_name,
            allow_duplicate=allow_duplicate,
            **kwargs,
        )

    # ------------------------------------------------------------------
    def get_callback_conflicts(self) -> Dict[str, List[str]]:
        """Return mapping of output identifiers to conflicting callback IDs.

        Thread-safe via an internal ``RLock``.
        """
        conflicts: Dict[str, List[str]] = {}
        seen: Dict[str, str] = {}
        with self._lock:
            for cid, reg in self._dash_callbacks.items():
                for o in reg.outputs:
                    key = f"{o.component_id}.{o.component_property}"
                    if key in seen and seen[key] != cid:
                        conflicts.setdefault(key, [seen[key]]).append(cid)
                    else:
                        seen[key] = cid
        return conflicts

    @property
    def registered_callbacks(self) -> Dict[str, DashCallbackRegistration]:
        """Thread-safe copy of registered callbacks."""
        with self._lock:
            return dict(self._dash_callbacks)

    # ------------------------------------------------------------------
    def print_callback_summary(self) -> None:
        """Log a summary of registered callbacks grouped by namespace.

        Thread-safe via an internal ``RLock``.
        """
        with self._lock:
            for namespace, ids in self._namespaces.items():
                logger.info(f"Callbacks for {namespace}:")
                for cid in ids:
                    reg = self._dash_callbacks[cid]
                    outputs_str = ", ".join(
                        f"{o.component_id}.{o.component_property}" for o in reg.outputs
                    )
                    logger.info(f"  {cid} -> {outputs_str}")

    # Event callbacks ---------------------------------------------------
    def register_event(
        self,
        event: CallbackEvent,
        func: CallbackHandler,
        *,
        priority: int = 50,
        secure: bool = False,
        timeout: Optional[float] = None,
        retries: int = 0,
    ) -> None:
        """Register an event callback.

        Thread-safe via an internal ``RLock``.
        """

        if secure:
            original = func

            def wrapped(*args: Any, **kwargs: Any) -> Any:
                if args and isinstance(args[0], str):
                    result = self.security.validate_input(args[0], "input")
                    if not result["valid"]:
                        logger.error(f"Security validation failed: {result['issues']}")
                        return None
                    args = (result["sanitized"],) + args[1:]
                return original(*args, **kwargs)

            func = wrapped

        with self._lock:
            self.event_bus.subscribe(event, func, priority=priority)

    # ------------------------------------------------------------------
    def unregister_event(self, event: CallbackEvent, func: CallbackHandler) -> None:
        """Remove a previously registered event callback.

        Thread-safe via an internal ``RLock``.
        """

        with self._lock:
            self.event_bus.unsubscribe(event, func)

    # ------------------------------------------------------------------
    def trigger_event(
        self, event: CallbackEvent, *args: Any, **kwargs: Any
    ) -> List[Any]:
        """Synchronously trigger callbacks registered for *event*."""

        return self.event_bus.emit(event, *args, **kwargs)

    async def trigger_event_async(
        self, event: CallbackEvent, *args: Any, **kwargs: Any
    ) -> List[Any]:
        """Asynchronously trigger callbacks registered for *event*.

        Callbacks are executed concurrently using ``asyncio`` when possible.
        """

        return await self.event_bus.emit_async(event, *args, **kwargs)

    def get_event_callbacks(self, event: CallbackEvent) -> List[CallbackHandler]:
        """Return registered callbacks for *event*.

        Thread-safe via an internal ``RLock``.
        """
        with self._lock:
            return self.event_bus.get_callbacks(event)

    def get_event_metrics(self, event: CallbackEvent) -> CallbackMetrics:
        """Return execution metrics for *event*.

        Thread-safe via an internal ``RLock``.
        """

        with self._lock:
            return self.event_bus.get_metrics(event)

    def clear_all_callbacks(self) -> None:
        """Remove all registered event callbacks."""

        with self._lock:
            self.event_bus.clear()

    # Operation groups --------------------------------------------------
    def register_operation(
        self,
        group: str,
        func: CallbackHandler,
        *,
        name: Optional[str] = None,
        timeout: Optional[float] = None,
        retries: int = 0,
    ) -> None:
        """Register an operation under a group name.

        Thread-safe via an internal ``RLock``.
        """
        op = Operation(name or func.__name__, func, timeout, retries)
        with self._lock:
            self._groups[group].append(op)

    def clear_group(self, group: str) -> None:
        """Clear registered operations for *group*.

        Thread-safe via an internal ``RLock``.
        """
        with self._lock:
            self._groups.pop(group, None)

    def execute_group(self, group: str, *args: Any, **kwargs: Any) -> List[Any]:
        """Execute all operations in a group sequentially.

        Thread-safe via an internal ``RLock`` when accessing group definitions.
        """
        from ...core.error_handling import ErrorSeverity, error_handler, with_retry

        results: List[Any] = []
        with self._lock:
            operations = list(self._groups.get(group, []))
        for op in operations:
            wrapped = with_retry(max_attempts=op.retries + 1)(op.func)
            start = time.perf_counter()
            try:
                result = wrapped(*args, **kwargs)
                duration = time.perf_counter() - start
                if op.timeout and duration > op.timeout:
                    raise TimeoutError(f"Operation {op.name} exceeded {op.timeout}s")
                results.append(result)
            except Exception as exc:  # pragma: no cover - log and continue
                error_handler.handle_error(
                    exc,
                    severity=ErrorSeverity.HIGH,
                    context={"operation": op.name, "group": group},
                )
                results.append(None)
        return results

    async def execute_group_async(
        self, group: str, *args: Any, **kwargs: Any
    ) -> List[Any]:
        """Execute all operations in a group concurrently.

        Thread-safe via an internal ``RLock`` when accessing group definitions.
        """
        from ...core.error_handling import ErrorSeverity, error_handler, with_retry

        async def _run(op: Operation) -> Any:
            wrapped = with_retry(max_attempts=op.retries + 1)(op.func)
            start = time.perf_counter()
            try:
                if asyncio.iscoroutinefunction(wrapped):
                    result = await wrapped(*args, **kwargs)
                else:
                    result = wrapped(*args, **kwargs)
                duration = time.perf_counter() - start
                if op.timeout and duration > op.timeout:
                    raise TimeoutError(f"Operation {op.name} exceeded {op.timeout}s")
                return result
            except Exception as exc:  # pragma: no cover - log and continue
                error_handler.handle_error(
                    exc,
                    severity=ErrorSeverity.HIGH,
                    context={"operation": op.name, "group": group},
                )
                return None

        with self._lock:
            operations = list(self._groups.get(group, []))

        tasks = [asyncio.create_task(_run(op)) for op in operations]
        return await asyncio.gather(*tasks) if tasks else []

    # ------------------------------------------------------------------
    def register_component_callbacks(
        self, component_class: Type[ComponentCallbackManager]
    ) -> None:
        """Register all callbacks from a component in one consolidated call."""

        component_id = getattr(
            component_class, "COMPONENT_ID", component_class.__name__
        )

        if component_id in self._registered_components:
            logger.warning(f"Component {component_id} already registered, skipping")
            return

        try:
            component = component_class()
            if hasattr(component, "register_callbacks"):
                component.register_callbacks(self)
                self._registered_components.add(component_id)
                logger.info(f"Registered callbacks for {component_id}")
        except Exception as e:  # pragma: no cover - defensive
            logger.error(f"Failed to register {component_id}: {e}")

    # ------------------------------------------------------------------
    def register_upload_callbacks(self, controller: Any | None = None) -> None:
        """Register upload related callbacks from a controller."""

        if controller is None:
            try:
                from ...services.upload.controllers.upload_controller import (
                    UnifiedUploadController,
                )
            except Exception as exc:  # pragma: no cover - import errors logged
                logger.error(f"Failed to import UnifiedUploadController: {exc}")
                return

            controller = UnifiedUploadController(callbacks=self)

        callback_sources = [
            getattr(controller, "upload_callbacks", lambda: [])(),
            getattr(controller, "progress_callbacks", lambda: [])(),
            getattr(controller, "validation_callbacks", lambda: [])(),
        ]

        for defs in callback_sources:
            for func, outputs, inputs, states, cid, extra in defs:
                self.register_handler(
                    outputs,
                    inputs,
                    states,
                    callback_id=cid,
                    component_name="file_upload",
                    **extra,
                )(func)

    # ------------------------------------------------------------------
    def register_all_callbacks(
        self, *manager_classes: type["ComponentCallbackManager"]
    ) -> None:
        """Instantiate and register callbacks from provided managers.

        If no ``manager_classes`` are provided, all classes registered on
        :class:`ComponentCallbackManager` via the :class:`~src.common.meta.AutoRegister`
        metaclass are used.
        """

        if not manager_classes:
            manager_classes = tuple(ComponentCallbackManager.REGISTRY.values())

        class _Registry(CallbackRegistry):
            def __init__(self, coord: "TrulyUnifiedCallbacks") -> None:
                super().__init__(coord.app)
                self._coord = coord

            def handle_register(
                self,
                outputs: Output | Iterable[Output],
                inputs: Iterable[Input] | Input | None = None,
                states: Iterable[State] | State | None = None,
                **kwargs: Any,
            ) -> Callable[[CallbackHandler], CallbackHandler]:
                return self._coord.handle_register(outputs, inputs, states, **kwargs)

        for manager_cls in manager_classes:
            registry = _Registry(self)
            manager = manager_cls(registry)
            self._namespaces.setdefault(manager.component_name, [])
            manager.register_all()

    # Compatibility wrappers -------------------------------------------
    register_callback = register_event  # noqa: F811
    unregister_callback = unregister_event
    trigger = trigger_event
    trigger_async = trigger_event_async
    get_callbacks = get_event_callbacks
    get_metrics = get_event_metrics


__all__ = ["TrulyUnifiedCallbacks", "CallbackHandler"]
