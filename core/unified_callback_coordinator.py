from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Callable, Dict, Iterable, List, Tuple
import threading
import logging

from dash import Dash
from dash.dependencies import Output, Input, State

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class CallbackRegistration:
    callback_id: str
    component_name: str
    outputs: Tuple[Output, ...]
    inputs: Tuple[Input, ...]
    states: Tuple[State, ...]


class UnifiedCallbackCoordinator:
    """Thread-safe callback registration with namespace tracking."""

    def __init__(self, app: Dash) -> None:
        self.app = app
        self._lock = threading.Lock()
        self._registrations: Dict[str, CallbackRegistration] = {}
        self._output_map: Dict[str, str] = {}
        self._namespaces: Dict[str, List[str]] = {}

    # ------------------------------------------------------------------
    def register_component_namespace(self, component_name: str) -> None:
        """Ensure a namespace exists for the given component."""
        with self._lock:
            self._namespaces.setdefault(component_name, [])

    # ------------------------------------------------------------------
    def register_callback(
        self,
        outputs: Any,
        inputs: Iterable[Input] | Input | None = None,
        states: Iterable[State] | State | None = None,
        *,
        callback_id: str,
        component_name: str,
        **kwargs: Any,
    ) -> Callable[[Callable[..., Any]], Callable[..., Any]]:
        """Wrap ``Dash.callback`` and track registrations."""

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
                if callback_id in self._registrations:
                    raise ValueError(f"Callback ID '{callback_id}' already registered")
                for o in outputs_tuple:
                    key = f"{o.component_id}.{o.component_property}"
                    if key in self._output_map:
                        raise ValueError(
                            f"Output '{key}' already used by callback '{self._output_map[key]}'"
                        )

                wrapped = self.app.callback(
                    outputs,
                    inputs_arg if inputs_arg is not None else inputs_tuple,
                    states_arg if states_arg is not None else states_tuple,
                    **kwargs,
                )(func)

                reg = CallbackRegistration(
                    callback_id=callback_id,
                    component_name=component_name,
                    outputs=tuple(outputs_tuple),
                    inputs=inputs_tuple,
                    states=states_tuple,
                )
                self._registrations[callback_id] = reg
                for o in outputs_tuple:
                    key = f"{o.component_id}.{o.component_property}"
                    self._output_map[key] = callback_id
                self._namespaces.setdefault(component_name, []).append(callback_id)
                return wrapped

        return decorator

    # ------------------------------------------------------------------
    @property
    def registered_callbacks(self) -> Dict[str, CallbackRegistration]:
        with self._lock:
            return dict(self._registrations)

    # ------------------------------------------------------------------
    def get_callback_conflicts(self) -> Dict[str, List[str]]:
        """Return mapping of output identifiers to callback IDs that conflict."""
        conflicts: Dict[str, List[str]] = {}
        seen: Dict[str, str] = {}
        with self._lock:
            for cid, reg in self._registrations.items():
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
                    reg = self._registrations[cid]
                    outputs_str = ", ".join(
                        f"{o.component_id}.{o.component_property}" for o in reg.outputs
                    )
                    logger.info("  %s -> %s", cid, outputs_str)



