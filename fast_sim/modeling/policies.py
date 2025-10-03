"""Policy hooks that mutate state during a run."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Callable, Literal, Protocol

from ..core.rng import RNG
from ..core.state import State
from ..core.timeline import Schedule


class PolicyFn(Protocol):
    def __call__(self, state: State, rng: RNG, t: float, context: dict[str, object]) -> None:
        ...


@dataclass
class Policy:
    name: str
    when: Literal["time-step", "event"]
    func: PolicyFn
    schedule: Schedule | None = None

    def apply(self, state: State, rng: RNG, t: float, context: dict[str, object]) -> None:
        self.func(state, rng, t, context)

    @classmethod
    def every(
        cls,
        name: str,
        when: Literal["time-step", "event"],
        interval: float,
        func: PolicyFn,
        start: float = 0.0,
    ) -> "Policy":
        return cls(name=name, when=when, func=func, schedule=Schedule(every=interval, start=start))

    @classmethod
    def at_times(
        cls,
        name: str,
        when: Literal["time-step", "event"],
        times: list[float],
        func: PolicyFn,
    ) -> "Policy":
        return cls(name=name, when=when, func=func, schedule=Schedule(at=times))
