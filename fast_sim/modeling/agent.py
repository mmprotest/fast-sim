"""Base agent primitive."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Tuple

from ..core.rng import RNG
from ..core.state import State


@dataclass
class Agent:
    """Minimal base class for stateful agents."""

    id: int
    fields: Tuple[str, ...]

    def tick(self, state: State, rng: RNG, t: float) -> None:  # pragma: no cover - default no-op
        return None

    def handle_event(self, state: State, rng: RNG, t: float, event: object) -> None:  # pragma: no cover - default no-op
        return None
