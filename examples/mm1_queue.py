"""Full M/M/1 queue discrete-event simulation example.

The example models a single-server queue with exponential inter-arrivals
and service times.  It demonstrates how to drive the
:class:`fast_sim.EventEngine`, collect queue length statistics, and run
what-if scenarios by tweaking arrival or service rates.

Execute directly from the project root:

.. code-block:: bash

    python examples/mm1_queue.py
"""
from __future__ import annotations

from dataclasses import dataclass

from fast_sim import EventEngine, Metrics, RNG, State
from fast_sim.core.event_queue import Event, EventQueue
from fast_sim.examples.mm1_queue import ARRIVAL, mm1_event_handler


@dataclass
class QueueResult:
    """Result bundle for :func:`simulate_mm1`."""

    state: State
    metrics: Metrics
    events_processed: int


def simulate_mm1(
    *,
    arrival_rate: float = 0.85,
    service_rate: float = 1.0,
    until: float = 200.0,
    seed: int = 42,
) -> QueueResult:
    """Run an M/M/1 queue simulation."""

    state = State(1)
    state.add_field("queue_length", int, 0)
    state.add_field("busy", int, 0)
    state.add_field("arrivals", int, 0)
    state.add_field("departures", int, 0)
    state.add_field("arrival_rate", float, arrival_rate)
    state.add_field("service_rate", float, service_rate)

    rng = RNG(seed)
    metrics = Metrics()

    def handler(state: State, rng: RNG, t: float, queue: EventQueue, event: Event) -> None:
        mm1_event_handler(state, rng, t, queue, event)
        metrics.observe("queue_length", float(state["queue_length"][0]), t)
        metrics.observe("busy", float(state["busy"][0]), t)
        metrics.observe("arrivals", float(state["arrivals"][0]), t)
        metrics.observe("departures", float(state["departures"][0]), t)

    engine = EventEngine(state, start_time=0.0, rng=rng, handle_event_fn=handler, metrics=metrics)
    engine.schedule(time=0.0, kind=ARRIVAL)
    summary = engine.run(until=until, progress=False)
    return QueueResult(state=state, metrics=metrics, events_processed=summary.events)


def main() -> None:
    result = simulate_mm1()
    final_queue = int(result.state["queue_length"][0])
    utilisation = result.metrics.rate("busy", window=10.0)
    total_arrivals = int(result.state["arrivals"][0])
    total_departures = int(result.state["departures"][0])

    print("Queue statistics after the run:")
    print(f"  Events processed : {result.events_processed}")
    print(f"  Queue length     : {final_queue}")
    print(f"  Utilisation (≈)  : {utilisation:.2f}")
    print(f"  Arrivals         : {total_arrivals}")
    print(f"  Departures       : {total_departures}")


if __name__ == "__main__":
    main()
