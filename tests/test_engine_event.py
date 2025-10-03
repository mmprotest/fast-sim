from fast_sim.core.engine_event import EventEngine
from fast_sim.core.metrics import Metrics
from fast_sim.core.rng import RNG
from fast_sim.core.state import State
from fast_sim.examples.mm1_queue import ARRIVAL, build_mm1_config, mm1_event_handler


def test_mm1_queue_invariants():
    cfg = build_mm1_config(arrival_rate=0.7, service_rate=1.0)
    rng = RNG(321)
    state = State(cfg.state.size)
    for name, field in cfg.state.fields.items():
        state.add_field(name, field.dtype, field.init)
    metrics = Metrics()
    engine = EventEngine(state, start_time=0.0, rng=rng, handle_event_fn=mm1_event_handler, metrics=metrics)
    for event in cfg.engine.initial_events:
        engine.schedule(time=event.get("time", 0.0), kind=event["kind"], payload=event.get("payload"))
    summary = engine.run(until=50.0, progress=False)
    assert summary.events > 0
    assert state["queue_length"][0] >= 0
    assert state["departures"][0] <= state["arrivals"][0]
    assert state["busy"][0] in {0, 1}
