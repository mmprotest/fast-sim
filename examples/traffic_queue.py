"""Simple traffic queue example."""
from __future__ import annotations

from pathlib import Path

import numpy as np

from fast_sim import Simulation, load_config
from fast_sim.agents import queue_step

CONFIG_PATH = Path(__file__).parent / "configs" / "traffic_demo.yaml"


def main() -> None:
    cfg = load_config(CONFIG_PATH)
    sim = Simulation.from_config(cfg, agent_step=queue_step)
    agents = np.zeros((cfg.n_agents, 2), dtype=float)
    sim.state["agents"] = agents
    sim.register_metric("queue_length", lambda state: float(state["agents"][:, 0].sum()))
    sim.register_metric("mean_wait", lambda state: float(state["agents"][:, 1].mean()))
    metrics = sim.run(cfg.steps)
    print("step\tqueue_length\tmean_wait")
    for idx, (length, wait) in enumerate(zip(metrics["queue_length"], metrics["mean_wait"])):
        print(f"{idx}\t{length:.2f}\t{wait:.2f}")


if __name__ == "__main__":
    main()
