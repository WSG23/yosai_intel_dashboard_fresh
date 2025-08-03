"""Stub prometheus counter for optional dependency tracking."""


class _Counter:
    def labels(self, **kwargs):  # pragma: no cover - simple stub
        return self

    def inc(self) -> None:  # pragma: no cover - simple stub
        pass


missing_dependencies = _Counter()

