from __future__ import annotations

import numpy as np

from fast_sim import Simulation, SimConfig
from fast_sim.agents import sir_step


def run_once(seed: int) -> tuple[np.ndarray, np.ndarray]:
    cfg = SimConfig(n_agents=20, steps=5, seed=seed, params={"model": "sir", "initial_infected": 2})
    sim = Simulation.from_config(cfg, agent_step=sir_step)
    agents = np.zeros((cfg.n_agents, 1), dtype=float)
    agents[:2, 0] = 1
    sim.state["agents"] = agents
    sim.register_metric("I", lambda state: float(np.sum(state["agents"][:, 0] == 1)))
    metrics = sim.run(cfg.steps)
    return sim.state["agents"].copy(), metrics["I"].copy()


def test_rng_determinism() -> None:
    state_a, metrics_a = run_once(123)
    state_b, metrics_b = run_once(123)
    assert np.array_equal(state_a, state_b)
    assert np.array_equal(metrics_a, metrics_b)
