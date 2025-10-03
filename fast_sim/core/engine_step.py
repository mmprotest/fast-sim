"""Time-step simulation engine."""
from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Callable, Sequence

from rich.progress import Progress

from .metrics import Metrics
from .rng import RNG
from .state import State
from .timeline import Timeline
from .tracing import Tracer, build_tracer
from ..modeling.policies import Policy


@dataclass
class RunSummary:
    steps: int
    end_time: float
    metrics: Metrics

    def metrics_frame(self) -> "pd.DataFrame":  # pragma: no cover - late import
        import pandas as pd

        return self.metrics.to_frame()


class StepEngine:
    """Execute a vectorised simulation advancing by a fixed ``dt``."""

    def __init__(
        self,
        state: State,
        timeline: Timeline,
        rng: RNG,
        tick_fn: Callable[[State, RNG, float], None],
        metrics: Metrics | None = None,
        policies: Sequence[Policy] | None = None,
        tracer: Tracer | None = None,
    ) -> None:
        self.state = state
        self.timeline = timeline
        self.rng = rng
        self.tick_fn = tick_fn
        self.metrics = metrics or Metrics()
        self.policies = list(policies or [])
        self.tracer = tracer or build_tracer(enabled=False)

    def _apply_policies(self, t: float, context: dict[str, float]) -> None:
        for policy in self.policies:
            if policy.when != "time-step":
                continue
            if policy.schedule is not None and not policy.schedule.is_due(t):
                continue
            policy.apply(self.state, self.rng, t, context)

    def run(self, progress: bool = True) -> RunSummary:
        steps = math.ceil(self.timeline.horizon / self.timeline.dt)
        progress_bar: Progress | None = None
        if progress:
            progress_bar = Progress(transient=True)
            progress_bar.__enter__()
            task_id = progress_bar.add_task("running", total=steps)
        else:
            task_id = None
        t = self.timeline.t
        for step in range(steps):
            context = {"step": step, "mode": "time-step"}
            self._apply_policies(t, context)
            self.tick_fn(self.state, self.rng, t)
            self.tracer.record("tick", step=step, t=t)
            t, done = self.timeline.tick()
            if progress_bar is not None and task_id is not None:
                progress_bar.update(task_id, advance=1)
            if done:
                break
        if progress_bar is not None:
            progress_bar.__exit__(None, None, None)
        return RunSummary(steps=self.timeline.steps, end_time=self.timeline.t, metrics=self.metrics)
