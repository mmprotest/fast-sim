"""Traffic cellular automaton simulation example.

This script configures a single-lane ring road where cars follow the
Nagel–Schreckenberg rules.  It illustrates how to model agent-based
systems with the :class:`fast_sim.StepEngine` and capture throughput
metrics at every step.

Run directly with:

.. code-block:: bash

    python examples/traffic_cellular_automata.py
"""
from __future__ import annotations

import random
from dataclasses import dataclass

from fast_sim import Metrics, RNG, State, StepEngine, Timeline
from fast_sim.examples.traffic_ca import traffic_tick


@dataclass
class TrafficResult:
    """Return type for :func:`simulate_traffic`."""

    state: State
    metrics: Metrics
    steps: int


def simulate_traffic(
    *,
    length: int = 60,
    density: float = 0.35,
    vmax: int = 5,
    slow_prob: float = 0.25,
    steps: int = 200,
    seed: int = 999,
) -> TrafficResult:
    """Simulate a cellular-automaton traffic model."""

    cars = int(length * density)
    road = [-1 for _ in range(length)]
    for idx in range(cars):
        road[idx] = idx
    random.Random(seed).shuffle(road)
    velocity = [0 for _ in range(length)]

    state = State(length)
    state.add_field("road", int, road)
    state.add_field("velocity", int, velocity)
    state.add_field("vmax", int, vmax)
    state.add_field("slow_prob", float, slow_prob)

    rng = RNG(seed)
    timeline = Timeline(t0=0.0, dt=1.0, horizon=float(steps))
    metrics = Metrics()

    def tick(state: State, rng: RNG, t: float) -> None:
        traffic_tick(state, rng, t)
        occupied = [idx for idx, cell in enumerate(state["road"]) if cell >= 0]
        if not occupied:
            return
        total_speed = sum(state["velocity"][idx] for idx in occupied)
        avg_speed = total_speed / len(occupied)
        metrics.observe("avg_speed", float(avg_speed), t)
        metrics.observe("density", float(len(occupied)) / len(state["road"]), t)

    engine = StepEngine(state, timeline, rng, tick, metrics=metrics)
    summary = engine.run(progress=False)
    return TrafficResult(state=state, metrics=metrics, steps=summary.steps)


def main() -> None:
    result = simulate_traffic()
    avg_speed_series = result.metrics.series.get("avg_speed", [])
    if avg_speed_series:
        last_speed = avg_speed_series[-1][1]
        overall_avg = sum(speed for _, speed in avg_speed_series) / len(avg_speed_series)
    else:
        last_speed = 0.0
        overall_avg = 0.0

    print("Traffic summary:")
    print(f"  Steps simulated : {result.steps}")
    print(f"  Cars on road    : {sum(1 for cell in result.state['road'] if cell >= 0)}")
    print(f"  Last avg speed  : {last_speed:.2f}")
    print(f"  Mean avg speed  : {overall_avg:.2f}")


if __name__ == "__main__":
    main()
