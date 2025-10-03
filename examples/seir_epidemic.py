"""Full SEIR epidemic simulation example.

This example demonstrates how to build a classic compartmental
susceptible-exposed-infectious-recovered (SEIR) model using the
:class:`fast_sim.StepEngine`.  It shows how to set up the simulation
state, advance it over time, and collect simple metrics that can later be
analysed or plotted.

Run it directly to execute the simulation and print a small summary:

.. code-block:: bash

    python examples/seir_epidemic.py
"""
from __future__ import annotations

from collections import Counter
from dataclasses import dataclass

from fast_sim import Metrics, RNG, State, StepEngine, Timeline
from fast_sim.examples.seir_epidemic import (
    EXPOSED,
    INFECTIOUS,
    RECOVERED,
    SUSCEPTIBLE,
    seir_tick,
)


@dataclass
class SeirResult:
    """Container returned by :func:`simulate_seir`."""

    state: State
    metrics: Metrics
    summary: dict[str, int]


def simulate_seir(
    *,
    population: int = 200,
    beta: float = 0.25,
    sigma: float = 0.2,
    gamma: float = 0.1,
    days: float = 120.0,
    seed: int = 123,
) -> SeirResult:
    """Run an SEIR simulation and collect summary metrics."""

    state = State(population)
    state.add_field("status", int, [SUSCEPTIBLE] * (population - 5) + [INFECTIOUS] * 5)
    state.add_field("beta", float, beta)
    state.add_field("sigma", float, sigma)
    state.add_field("gamma", float, gamma)

    rng = RNG(seed)
    timeline = Timeline(t0=0.0, dt=1.0, horizon=days)
    metrics = Metrics()

    def tick(state: State, rng: RNG, t: float) -> None:
        seir_tick(state, rng, t)
        counts = Counter(state["status"])
        metrics.observe("susceptible", float(counts.get(SUSCEPTIBLE, 0)), t)
        metrics.observe("exposed", float(counts.get(EXPOSED, 0)), t)
        metrics.observe("infectious", float(counts.get(INFECTIOUS, 0)), t)
        metrics.observe("recovered", float(counts.get(RECOVERED, 0)), t)

    engine = StepEngine(state, timeline, rng, tick, metrics=metrics)
    engine.run(progress=False)

    final_counts = Counter(state["status"])
    summary = {
        "susceptible": final_counts.get(SUSCEPTIBLE, 0),
        "exposed": final_counts.get(EXPOSED, 0),
        "infectious": final_counts.get(INFECTIOUS, 0),
        "recovered": final_counts.get(RECOVERED, 0),
    }
    return SeirResult(state=state, metrics=metrics, summary=summary)


def main() -> None:
    result = simulate_seir()
    print("Final compartment sizes:")
    for name, value in result.summary.items():
        print(f"  {name.title():<12}: {value}")

    infectious_series = result.metrics.series.get("infectious", [])
    if infectious_series:
        peak_time, peak_value = max(infectious_series, key=lambda entry: entry[1])
        print(f"\nPeak infectious count: {int(peak_value)} on day {peak_time:.0f}")


if __name__ == "__main__":
    main()
