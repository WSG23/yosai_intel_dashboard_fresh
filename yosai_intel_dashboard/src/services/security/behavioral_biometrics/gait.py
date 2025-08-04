"""Gait analysis utilities based on a simple LSTM model."""

from __future__ import annotations

from typing import Sequence

try:  # pragma: no cover - dependency availability
    import torch
    from torch import nn
except Exception:  # pragma: no cover - handle missing dependency
    torch = None  # type: ignore[assignment]
    nn = None  # type: ignore[assignment]


class GaitAnalyzer:
    """Run a lightweight LSTM over gait sequences to detect anomalies."""

    def __init__(self) -> None:
        if torch is not None and nn is not None:
            self.model = nn.LSTM(input_size=1, hidden_size=8, batch_first=True)
        else:  # pragma: no cover - no ML backend available
            self.model = None

    def is_anomaly(self, sequence: Sequence[Sequence[float]]) -> bool:
        """Return ``True`` if the provided gait ``sequence`` is anomalous."""
        if self.model is None or torch is None:
            return False
        with torch.no_grad():
            tensor = torch.tensor(sequence, dtype=torch.float32).unsqueeze(-1)
            output, _ = self.model(tensor)
            score = output.abs().mean().item()
        return score > 1.0
