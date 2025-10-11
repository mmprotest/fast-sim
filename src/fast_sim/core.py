"""Core simulation loop implementation."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Callable, Dict, Mapping, MutableMapping

import numpy as np

from .config import SimConfig
from .metrics import MetricRecorder
from .random import get_rng
from .scheduler import StepHooks

AgentUpdater = Callable[[Dict[str, np.ndarray], Dict[str, Any], np.random.Generator], None]
MetricExtractor = Callable[[Dict[str, np.ndarray]], np.ndarray | float]


@dataclass
class Simulation:
    """Vectorised agent-based simulation runner."""

    state: Dict[str, np.ndarray]
    params: Dict[str, Any]
    record_every: int
    hooks: StepHooks = field(default_factory=StepHooks)
    metrics: MutableMapping[str, np.ndarray] = field(default_factory=dict)
    agent_step: AgentUpdater | None = None

    def __post_init__(self) -> None:
        self._metric_extractors: Dict[str, MetricExtractor] = {}

    @classmethod
    def from_config(cls, cfg: SimConfig, agent_step: AgentUpdater | None = None) -> "Simulation":
        """Create a simulation from a :class:`SimConfig` instance."""

        cfg.apply_seed()
        state = cls._init_state(cfg)
        sim = cls(state=state, params=dict(cfg.params), record_every=cfg.record_every)
        sim.agent_step = agent_step
        return sim

    @staticmethod
    def _init_state(cfg: SimConfig) -> Dict[str, np.ndarray]:
        agents = np.zeros((cfg.n_agents, 1), dtype=float)
        return {"agents": agents, "time": np.zeros(1, dtype=int)}

    def register_metric(
        self,
        name: str,
        extractor: MetricExtractor | None = None,
    ) -> None:
        """Register a metric to record each step."""

        if hasattr(self, "_recorder"):
            raise RuntimeError("Metrics already initialised; register metrics before running.")
        self._metric_extractors[name] = extractor or (lambda state: float(state["agents"].sum()))

    def _ensure_recorder(self, steps: int) -> MetricRecorder:
        if hasattr(self, "_recorder"):
            return self._recorder  # type: ignore[attr-defined]
        names = list(self._metric_extractors) or ["agents"]
        capacity = (steps + self.record_every - 1) // self.record_every
        self._recorder = MetricRecorder(names, capacity)
        return self._recorder

    def _step(self, step: int, recorder: MetricRecorder) -> None:
        rng = get_rng()
        self.hooks.trigger("on_step_start", self.state, self.params, step)
        if self.agent_step is not None:
            self.agent_step(self.state, self.params, rng)
        self.hooks.trigger("update_agents", self.state, self.params, step)
        self.hooks.trigger("update_world", self.state, self.params, step)
        if step % self.record_every == 0:
            if not self._metric_extractors:
                self.register_metric("agents")
            for name, extractor in self._metric_extractors.items():
                value = extractor(self.state)
                recorder.record(name, value)
            self.hooks.trigger("record_metrics", self.state, self.params, step)
            recorder.next_step()
        self.hooks.trigger("on_step_end", self.state, self.params, step)
        self.state["time"][0] = step

    def run(self, steps: int) -> Mapping[str, np.ndarray]:
        """Run the simulation for the given number of steps."""

        recorder = self._ensure_recorder(steps)
        for step in range(steps):
            self._step(step, recorder)
        self.metrics = recorder.results()
        return self.metrics


__all__ = ["Simulation", "AgentUpdater", "MetricExtractor"]
