"""Minimal stub of rich.progress.Progress."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict


@dataclass
class Progress:
    transient: bool = True
    _tasks: Dict[int, float] = field(default_factory=dict)

    def __enter__(self) -> "Progress":  # pragma: no cover - trivial
        return self

    def __exit__(self, exc_type, exc, tb) -> None:  # pragma: no cover - trivial
        return None

    def add_task(self, description: str, total: float | None = None) -> int:
        task_id = len(self._tasks) + 1
        self._tasks[task_id] = 0.0
        return task_id

    def update(self, task_id: int, advance: float = 1.0) -> None:
        if task_id in self._tasks:
            self._tasks[task_id] += advance
