from __future__ import annotations

from typing import Any, Callable
import inspect


class CallbackUnifier:
    """Utility to unify callback registration across different managers."""

    def __init__(self, target: Any, safe_wrapper: Callable[[Callable], Callable] | None = None) -> None:
        self._target = target
        self._safe_wrapper = safe_wrapper

    # ------------------------------------------------------------------
    def __call__(
        self,
        outputs: Any,
        inputs: Any = None,
        states: Any = None,
        **kwargs: Any,
    ) -> Callable[[Callable[..., Any]], Callable[..., Any]]:
        """Return decorator registering callbacks on the wrapped target."""

        def decorator(func: Callable[..., Any]) -> Callable[..., Any]:
            wrapped = self._safe_wrapper(func) if self._safe_wrapper else func

            if hasattr(self._target, "register_callback"):
                try:
                    return self._target.register_callback(
                        outputs, inputs, states, **kwargs
                    )(wrapped)
                except TypeError:
                    sig = inspect.signature(self._target.register_callback)
                    filtered = {k: v for k, v in kwargs.items() if k in sig.parameters}
                    return self._target.register_callback(
                        outputs, inputs, states, **filtered
                    )(wrapped)
            if hasattr(self._target, "callback"):
                return self._target.callback(outputs, inputs, states, **kwargs)(wrapped)

            raise TypeError("Unsupported callback target")

        return decorator

