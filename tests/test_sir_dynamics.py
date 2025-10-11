from __future__ import annotations

import numpy as np

from fast_sim import Simulation, SimConfig
from fast_sim.agents import sir_step


def test_sir_infections_rise_then_fall() -> None:
    cfg = SimConfig(
        n_agents=200,
        steps=40,
        params={"model": "sir", "beta": 0.3, "gamma": 0.1, "initial_infected": 5},
    )
    sim = Simulation.from_config(cfg, agent_step=sir_step)
    agents = np.zeros((cfg.n_agents, 1), dtype=float)
    agents[:5, 0] = 1
    sim.state["agents"] = agents
    sim.register_metric("I", lambda state: float(np.sum(state["agents"][:, 0] == 1)))
    metrics = sim.run(cfg.steps)["I"]
    assert metrics.max() > metrics[0]
    peak_index = int(np.argmax(metrics))
    assert peak_index > 0
    assert metrics[-1] < metrics[peak_index]
