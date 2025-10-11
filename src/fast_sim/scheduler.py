"""Simulation scheduler supporting hook registration."""
from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass, field
from typing import Any, Dict, Iterable, List

import numpy as np

Hook = Callable[[Dict[str, np.ndarray], Dict[str, Any], int], None]


@dataclass
class StepHooks:
    """Container for lifecycle hooks."""

    on_step_start: List[Hook] = field(default_factory=list)
    update_agents: List[Hook] = field(default_factory=list)
    update_world: List[Hook] = field(default_factory=list)
    record_metrics: List[Hook] = field(default_factory=list)
    on_step_end: List[Hook] = field(default_factory=list)

    def add(self, stage: str, hook: Hook) -> None:
        """Register a hook for a stage."""

        if not hasattr(self, stage):
            raise ValueError(f"Unknown hook stage '{stage}'.")
        getattr(self, stage).append(hook)

    def trigger(self, stage: str, state: Dict[str, np.ndarray], params: Dict[str, Any], step: int) -> None:
        """Trigger all hooks in a stage."""

        hooks: Iterable[Hook] = getattr(self, stage)
        for hook in hooks:
            hook(state, params, step)


__all__ = ["StepHooks", "Hook"]
