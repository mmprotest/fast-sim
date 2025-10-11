"""Reference agent update functions."""
from __future__ import annotations

import numpy as np

from .random import get_rng


def sir_step(state: dict[str, np.ndarray], params: dict[str, float], rng: np.random.Generator | None = None) -> None:
    """Perform a SIR compartment update on the agent state."""

    if rng is None:
        rng = get_rng()
    agents = state.setdefault("agents", np.zeros((0, 1), dtype=int))
    if agents.size == 0:
        return
    beta = float(params.get("beta", 0.1))
    gamma = float(params.get("gamma", 0.05))
    compartments = agents[:, 0].astype(int)
    infected = compartments == 1
    susceptible = compartments == 0
    recovered = compartments == 2

    total = susceptible.sum() + infected.sum() + recovered.sum()
    if total == 0:
        return

    infection_pressure = infected.sum() / max(total, 1)
    new_infections = rng.binomial(1, np.clip(beta * infection_pressure, 0.0, 1.0), size=susceptible.sum())
    new_recoveries = rng.binomial(1, np.clip(gamma, 0.0, 1.0), size=infected.sum())

    sus_indices = np.where(susceptible)[0]
    inf_indices = np.where(infected)[0]
    agents[sus_indices[new_infections.astype(bool)], 0] = 1
    agents[inf_indices[new_recoveries.astype(bool)], 0] = 2


def queue_step(state: dict[str, np.ndarray], params: dict[str, float], rng: np.random.Generator | None = None) -> None:
    """Update a simple queue of agents representing cars."""

    if rng is None:
        rng = get_rng()
    agents = state.setdefault("agents", np.zeros((0, 2), dtype=float))
    if agents.size == 0:
        return
    arrival_rate = float(params.get("arrival_rate", 0.1))
    service_rate = float(params.get("service_rate", 0.2))

    queue_positions = agents[:, 0]
    wait_times = agents[:, 1]

    arrivals = rng.random(size=agents.shape[0]) < arrival_rate
    services = rng.random(size=agents.shape[0]) < service_rate

    queue_positions += arrivals.astype(float)
    served = services & (queue_positions > 0)
    queue_positions[served] -= 1.0
    wait_times += queue_positions

    state["agents"] = np.column_stack((queue_positions, wait_times))


__all__ = ["sir_step", "queue_step"]
