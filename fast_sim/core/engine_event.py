"""Discrete-event simulation engine."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Callable, Sequence

from rich.progress import Progress

from .event_queue import Event, EventQueue
from .metrics import Metrics
from .rng import RNG
from .state import State
from .tracing import Tracer, build_tracer
from ..modeling.policies import Policy


@dataclass
class EventRunSummary:
    events: int
    end_time: float
    metrics: Metrics

    def metrics_frame(self) -> "pd.DataFrame":  # pragma: no cover
        import pandas as pd

        return self.metrics.to_frame()


class EventEngine:
    """Process events from a priority queue until termination."""

    def __init__(
        self,
        state: State,
        start_time: float,
        rng: RNG,
        handle_event_fn: Callable[[State, RNG, float, EventQueue, Event], None],
        metrics: Metrics | None = None,
        policies: Sequence[Policy] | None = None,
        tracer: Tracer | None = None,
    ) -> None:
        self.state = state
        self.time = start_time
        self.rng = rng
        self.queue = EventQueue()
        self.handle_event_fn = handle_event_fn
        self.metrics = metrics or Metrics()
        self.policies = list(policies or [])
        self.tracer = tracer or build_tracer(enabled=False)

    def schedule(
        self,
        time: float,
        kind: str,
        payload: dict | None = None,
        target_id: int | None = None,
        priority: int = 0,
    ) -> None:
        event = Event(time=time, priority=priority, kind=kind, payload=payload or {}, target_id=target_id)
        self.queue.push(event)

    def _apply_policies(self, t: float, event: Event, count: int) -> None:
        context = {"event": event, "count": count, "mode": "event"}
        for policy in self.policies:
            if policy.when != "event":
                continue
            if policy.schedule is not None and not policy.schedule.is_due(t):
                continue
            policy.apply(self.state, self.rng, t, context)

    def run(
        self,
        until: float | None = None,
        max_events: int | None = None,
        progress: bool = True,
    ) -> EventRunSummary:
        processed = 0
        progress_bar: Progress | None = None
        total = max_events if max_events is not None else None
        if progress:
            progress_bar = Progress(transient=True)
            progress_bar.__enter__()
            task = progress_bar.add_task("events", total=total)
        else:
            task = None
        while len(self.queue) > 0:
            event = self.queue.pop()
            if until is not None and event.time > until:
                break
            self.time = event.time
            self._apply_policies(self.time, event, processed)
            self.handle_event_fn(self.state, self.rng, self.time, self.queue, event)
            self.tracer.record("event", event_kind=event.kind, t=self.time)
            processed += 1
            if progress_bar is not None and task is not None:
                progress_bar.update(task, advance=1)
            if max_events is not None and processed >= max_events:
                break
        if progress_bar is not None:
            progress_bar.__exit__(None, None, None)
        return EventRunSummary(events=processed, end_time=self.time, metrics=self.metrics)
