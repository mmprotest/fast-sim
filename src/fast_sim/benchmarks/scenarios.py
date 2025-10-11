"""Benchmark scenarios for fast_sim."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Callable, Dict

from fast_sim.agents import queue_step, sir_step
from fast_sim.config import SimConfig


@dataclass
class Scenario:
    """Definition of a benchmark scenario."""

    name: str
    config: SimConfig
    step_fn: Callable


def sir_scenario(n_agents: int, steps: int) -> Scenario:
    params = {"model": "sir", "beta": 0.12, "gamma": 0.04, "initial_infected": 5}
    cfg = SimConfig(n_agents=n_agents, steps=steps, params=params)
    return Scenario(name=f"sir_{n_agents}", config=cfg, step_fn=sir_step)


def queue_scenario(n_agents: int, steps: int) -> Scenario:
    params: Dict[str, float] = {"model": "queue", "arrival_rate": 0.3, "service_rate": 0.4}
    cfg = SimConfig(n_agents=n_agents, steps=steps, params=params)
    return Scenario(name=f"queue_{n_agents}", config=cfg, step_fn=queue_step)


SCENARIOS = [
    sir_scenario(1_000, 100),
    sir_scenario(10_000, 100),
    queue_scenario(1_000, 100),
    queue_scenario(10_000, 100),
]

__all__ = ["SCENARIOS", "Scenario"]
