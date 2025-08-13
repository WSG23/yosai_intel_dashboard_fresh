from core.types import BProtocol


class A:
    """Component depending on a BProtocol implementation.

    The dependency is injected through the constructor to avoid a
    compile‑time import of :mod:`B` which would create a circular import.
    """

    def __init__(self, b: BProtocol) -> None:
        self._b = b

    def do_a(self) -> str:
        """Delegate to the injected ``B`` implementation."""
        return f"A -> {self._b.do_b()}"
