"""Time management utilities."""
from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Iterable, Iterator, Sequence


class Timeline:
    """Utility for stepping through time with a fixed interval."""

    def __init__(self, t0: float, dt: float, horizon: float) -> None:
        if dt <= 0:
            raise ValueError("dt must be positive")
        if horizon <= 0:
            raise ValueError("horizon must be positive")
        self.t0 = t0
        self.dt = dt
        self.horizon = horizon
        self.end = t0 + horizon
        self.t = t0
        self.steps = 0

    def tick(self) -> tuple[float, bool]:
        """Advance time by ``dt`` and return ``(t, done)``."""

        if self.t >= self.end:
            return self.t, True
        self.t = round(self.t + self.dt, 12)
        self.steps += 1
        done = self.t >= self.end - 1e-12
        return self.t, done

    def reset(self) -> None:
        self.t = self.t0
        self.steps = 0

    def iter(self) -> Iterator[float]:
        while True:
            t, done = self.tick()
            yield t
            if done:
                break


@dataclass(slots=True)
class Schedule:
    """Schedule a callable at explicit times or on an interval."""

    at: Sequence[float] | None = None
    every: float | None = None
    start: float = 0.0

    def __post_init__(self) -> None:
        if self.at is None and self.every is None:
            raise ValueError("Schedule requires 'at' or 'every'")
        if self.every is not None and self.every <= 0:
            raise ValueError("'every' must be positive")
        if self.at is not None:
            self._sorted = sorted(self.at)
        else:
            self._sorted = []

    def is_due(self, t: float) -> bool:
        if self.at is not None:
            return any(math.isclose(t, when, rel_tol=0.0, abs_tol=1e-9) for when in self._sorted)
        if t < self.start - 1e-9:
            return False
        if self.every is None:
            return False
        elapsed = t - self.start
        k = round(elapsed / self.every)
        if k < 0:
            return False
        return math.isclose(elapsed, k * self.every, rel_tol=0.0, abs_tol=1e-9)

    def next_times(self, until: float) -> Iterable[float]:
        if self.at is not None:
            for when in self._sorted:
                if when <= until + 1e-9:
                    yield when
        elif self.every is not None:
            t = self.start
            while t <= until + 1e-9:
                yield round(t, 12)
                t += self.every
