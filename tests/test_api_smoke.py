from __future__ import annotations

import numpy as np

from fast_sim import Simulation, SimConfig
from fast_sim.agents import sir_step


def test_simulation_run_smoke() -> None:
    cfg = SimConfig(n_agents=10, steps=3, params={"model": "sir", "initial_infected": 2})
    sim = Simulation.from_config(cfg, agent_step=sir_step)
    agents = np.zeros((cfg.n_agents, 1), dtype=float)
    agents[:2, 0] = 1
    sim.state["agents"] = agents
    sim.register_metric("I", lambda state: float(np.sum(state["agents"][:, 0] == 1)))
    metrics = sim.run(cfg.steps)
    assert "I" in metrics
    assert metrics["I"].shape[0] == cfg.steps
