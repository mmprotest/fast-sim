"""Priority queue for discrete events."""
from __future__ import annotations

import heapq
from dataclasses import dataclass, field
from typing import Any


@dataclass(order=True)
class Event:
    time: float
    priority: int
    kind: str = field(compare=False)
    payload: dict[str, Any] = field(default_factory=dict, compare=False)
    target_id: int | None = field(default=None, compare=False)
    seq: int = field(default=0, compare=False)


class EventQueue:
    """Binary heap priority queue for :class:`Event` objects."""

    def __init__(self) -> None:
        self._heap: list[tuple[float, int, int, Event]] = []
        self._seq = 0

    def push(self, event: Event) -> None:
        self._seq += 1
        event.seq = self._seq
        heapq.heappush(self._heap, (event.time, event.priority, event.seq, event))

    def pop(self) -> Event:
        if not self._heap:
            raise IndexError("pop from empty EventQueue")
        _, _, _, event = heapq.heappop(self._heap)
        return event

    def peek_time(self) -> float | None:
        if not self._heap:
            return None
        return self._heap[0][0]

    def __len__(self) -> int:
        return len(self._heap)

    def clear(self) -> None:
        self._heap.clear()
        self._seq = 0
