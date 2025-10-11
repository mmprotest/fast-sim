"""Minimal SIR simulation example."""
from __future__ import annotations

from pathlib import Path

import numpy as np

from fast_sim import Simulation, load_config
from fast_sim.agents import sir_step

CONFIG_PATH = Path(__file__).parent / "configs" / "sir_demo.yaml"


def main() -> None:
    cfg = load_config(CONFIG_PATH)
    sim = Simulation.from_config(cfg, agent_step=sir_step)
    agents = np.zeros((cfg.n_agents, 1), dtype=float)
    agents[: cfg.params.get("initial_infected", 3), 0] = 1
    sim.state["agents"] = agents
    sim.register_metric("S", lambda state: float(np.sum(state["agents"][:, 0] == 0)))
    sim.register_metric("I", lambda state: float(np.sum(state["agents"][:, 0] == 1)))
    sim.register_metric("R", lambda state: float(np.sum(state["agents"][:, 0] == 2)))
    metrics = sim.run(cfg.steps)
    print("step\tS\tI\tR")
    for idx, (s, i, r) in enumerate(zip(metrics["S"], metrics["I"], metrics["R"])):
        print(f"{idx}\t{int(s)}\t{int(i)}\t{int(r)}")


if __name__ == "__main__":
    main()
