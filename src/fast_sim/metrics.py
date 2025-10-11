"""Simple metric recording utilities."""
from __future__ import annotations

from typing import Dict, Iterable, MutableMapping

import numpy as np


class MetricRecorder:
    """Record scalar or array metrics at fixed intervals."""

    def __init__(self, names: Iterable[str], capacity: int) -> None:
        self._names = list(names)
        self._capacity = int(capacity)
        self._store: Dict[str, np.ndarray] = {
            name: np.zeros(self._capacity, dtype=float) for name in self._names
        }
        self._cursor = 0

    def record(self, name: str, value: np.ndarray | float | int) -> None:
        """Record a value for the given metric name."""

        if name not in self._store:
            raise KeyError(f"Metric '{name}' is not registered.")
        if self._cursor >= self._capacity:
            return
        self._store[name][self._cursor] = float(np.asarray(value))

    def next_step(self) -> None:
        """Advance to the next time step."""

        if self._cursor < self._capacity:
            self._cursor += 1

    def results(self) -> MutableMapping[str, np.ndarray]:
        """Return the recorded metrics truncated to the cursor."""

        return {name: values[: self._cursor].copy() for name, values in self._store.items()}


__all__ = ["MetricRecorder"]
