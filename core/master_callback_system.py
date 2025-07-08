from __future__ import annotations

"""Unified callback system consolidating legacy implementations."""

import asyncio
import logging
import threading
import time
from collections import defaultdict
from dataclasses import dataclass
from typing import Any, Callable, Dict, Iterable, List, Optional, Tuple

from dash import Dash
from dash.dependencies import Input, Output, State

from .callback_events import CallbackEvent
from .error_handling import error_handler, ErrorSeverity, with_retry

logger = logging.getLogger(__name__)


@dataclass
class EventCallback:
    """Internal representation of an event callback."""

    priority: int
    func: Callable[..., Any]
    secure: bool = False
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


class MasterCallbackSystem:
    """Unified system providing event and Dash callback management."""

    def __init__(
        self,
        app: Optional[Dash] = None,
        *,
        security_validator: Optional["SecurityValidator"] = None,
    ) -> None:
        self.app = app
        if security_validator is None:
            from .security_validator import SecurityValidator

            self.security = SecurityValidator()
        else:
            self.security = security_validator
        self._lock = threading.RLock()
        self._event_callbacks: Dict[CallbackEvent, List[EventCallback]] = defaultdict(list)
        self._dash_callbacks: Dict[str, DashCallbackRegistration] = {}
        self._output_map: Dict[str, str] = {}
        self._namespaces: Dict[str, List[str]] = defaultdict(list)
        self._metrics: Dict[str, Dict[str, float | int]] = defaultdict(
            lambda: {"calls": 0, "errors": 0, "total_time": 0.0}
        )

    # ------------------------------------------------------------------
    def register_event_callback(
        self,
        event: CallbackEvent,
        func: Callable[..., Any],
        *,
        priority: int = 50,
        secure: bool = False,
        timeout: Optional[float] = None,
        retries: int = 0,
    ) -> None:
        """Register a callback for a :class:`CallbackEvent`."""
        if secure:
            original = func

            def wrapped(*args: Any, **kwargs: Any) -> Any:
                if args and isinstance(args[0], str):
                    result = self.security.validate_input(args[0], "input")
                    if not result["valid"]:
                        logger.error(
                            "Security validation failed: %s", result["issues"]
                        )
                        return None
                    args = (result["sanitized"],) + args[1:]
                return original(*args, **kwargs)

            func = wrapped

        cb = EventCallback(priority, func, secure, timeout, retries)
        with self._lock:
            self._event_callbacks[event].append(cb)
            self._event_callbacks[event].sort(key=lambda c: c.priority)

    # ------------------------------------------------------------------
    def trigger_event(self, event: CallbackEvent, *args: Any, **kwargs: Any) -> List[Any]:
        """Synchronously trigger callbacks registered for *event*."""
        results = []
        callbacks = list(self._event_callbacks.get(event, []))
        for cb in callbacks:
            wrapped = with_retry(max_attempts=cb.retries + 1)(cb.func)
            start = time.perf_counter()
            try:
                result = wrapped(*args, **kwargs)
                duration = time.perf_counter() - start
                if cb.timeout and duration > cb.timeout:
                    raise TimeoutError(f"Operation exceeded {cb.timeout}s")
                results.append(result)
                self._record_metric(event, start)
            except Exception as exc:  # pragma: no cover - log and continue
                error_handler.handle_error(
                    exc,
                    severity=ErrorSeverity.HIGH,
                    context={"event": event.name, "callback": cb.func.__name__},
                )
                self._record_metric(event, start, error=True)
                results.append(None)
        return results

    # ------------------------------------------------------------------
    async def trigger_event_async(self, event: CallbackEvent, *args: Any, **kwargs: Any) -> List[Any]:
        """Asynchronously trigger callbacks for *event*."""
        results = []
        callbacks = list(self._event_callbacks.get(event, []))
        for cb in callbacks:
            wrapped = with_retry(max_attempts=cb.retries + 1)(cb.func)
            start = time.perf_counter()
            try:
                if asyncio.iscoroutinefunction(cb.func):
                    result = await wrapped(*args, **kwargs)
                else:
                    result = wrapped(*args, **kwargs)
                duration = time.perf_counter() - start
                if cb.timeout and duration > cb.timeout:
                    raise TimeoutError(f"Operation exceeded {cb.timeout}s")
                results.append(result)
                self._record_metric(event, start)
            except Exception as exc:  # pragma: no cover - log and continue
                error_handler.handle_error(
                    exc,
                    severity=ErrorSeverity.HIGH,
                    context={"event": event.name, "callback": cb.func.__name__},
                )
                self._record_metric(event, start, error=True)
                results.append(None)
        return results

    # ------------------------------------------------------------------
    def register_dash_callback(
        self,
        outputs: Any,
        inputs: Iterable[Input] | Input | None = None,
        states: Iterable[State] | State | None = None,
        *,
        callback_id: str,
        component_name: str,
        allow_duplicate: bool = False,
        **kwargs: Any,
    ) -> Callable[[Callable[..., Any]], Callable[..., Any]]:
        """Register a Dash callback and track conflicts."""
        if self.app is None:
            raise RuntimeError("Dash app not configured for MasterCallbackSystem")

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

        def decorator(func: Callable[..., Any]) -> Callable[..., Any]:
            with self._lock:
                if callback_id in self._dash_callbacks:
                    raise ValueError(f"Callback ID '{callback_id}' already registered")

                for o in outputs_tuple:
                    key = f"{o.component_id}.{o.component_property}"
                    if key in self._output_map and not allow_duplicate:
                        raise ValueError(
                            f"Output '{key}' already used by callback '{self._output_map[key]}'"
                        )

                wrapped = self.app.callback(
                    outputs,
                    inputs_arg if inputs_arg is not None else inputs_tuple,
                    states_arg if states_arg is not None else states_tuple,
                    **kwargs,
                )(func)

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
    def get_callback_conflicts(self) -> Dict[str, List[str]]:
        """Return mapping of output identifiers to conflicting callback IDs."""
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

    # ------------------------------------------------------------------
    def print_callback_summary(self) -> None:
        """Log a summary of registered callbacks grouped by namespace."""
        with self._lock:
            for namespace, ids in self._namespaces.items():
                logger.info("Callbacks for %s:", namespace)
                for cid in ids:
                    reg = self._dash_callbacks[cid]
                    outputs_str = ", ".join(
                        f"{o.component_id}.{o.component_property}" for o in reg.outputs
                    )
                    logger.info("  %s -> %s", cid, outputs_str)

    # ------------------------------------------------------------------
    def _record_metric(self, event: CallbackEvent, start: float, error: bool = False) -> None:
        metric = self._metrics[event.name]
        metric["calls"] += 1
        if error:
            metric["errors"] += 1
        metric["total_time"] += time.perf_counter() - start

    # ------------------------------------------------------------------
    def get_metrics(self, event: CallbackEvent) -> Dict[str, float | int]:
        """Return execution metrics for *event*."""
        return dict(self._metrics.get(event.name, {}))


__all__ = ["MasterCallbackSystem"]
