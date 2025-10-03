"""M/M/1 queue discrete-event example."""
from __future__ import annotations

from ..core.event_queue import Event, EventQueue
from ..core.rng import RNG
from ..core.state import State
from ..io.config import Config

ARRIVAL = "ARRIVAL"
DEPARTURE = "DEPARTURE"


def mm1_event_handler(state: State, rng: RNG, t: float, queue: EventQueue, event: Event) -> None:
    queue_len = state["queue_length"]
    busy = state["busy"]
    arrivals = state["arrivals"]
    departures = state["departures"]
    arrival_rate = state["arrival_rate"][0]
    service_rate = state["service_rate"][0]

    if event.kind == ARRIVAL:
        arrivals[0] += 1
        interarrival_raw = rng.exponential(scale=1.0 / arrival_rate)
        interarrival = interarrival_raw if isinstance(interarrival_raw, float) else interarrival_raw[0]
        queue.push(Event(time=t + interarrival, priority=0, kind=ARRIVAL, payload={}))
        if busy[0] == 1:
            queue_len[0] += 1
        else:
            busy[0] = 1
            service_time_raw = rng.exponential(scale=1.0 / service_rate)
            service_time = service_time_raw if isinstance(service_time_raw, float) else service_time_raw[0]
            queue.push(Event(time=t + service_time, priority=1, kind=DEPARTURE, payload={}))
    elif event.kind == DEPARTURE:
        departures[0] += 1
        if queue_len[0] > 0:
            queue_len[0] -= 1
            service_time_raw = rng.exponential(scale=1.0 / service_rate)
            service_time = service_time_raw if isinstance(service_time_raw, float) else service_time_raw[0]
            queue.push(Event(time=t + service_time, priority=1, kind=DEPARTURE, payload={}))
        else:
            busy[0] = 0


def build_mm1_config(arrival_rate: float = 0.8, service_rate: float = 1.0) -> Config:
    data = {
        "seed": 42,
        "state": {
            "size": 1,
            "fields": {
                "queue_length": {"dtype": "int64", "init": 0},
                "busy": {"dtype": "int64", "init": 0},
                "arrivals": {"dtype": "int64", "init": 0},
                "departures": {"dtype": "int64", "init": 0},
                "arrival_rate": {"dtype": "float64", "init": arrival_rate},
                "service_rate": {"dtype": "float64", "init": service_rate},
            },
        },
        "engine": {
            "type": "event",
            "handler": "fast_sim.examples.mm1_queue:mm1_event_handler",
            "until": 100.0,
            "initial_events": [
                {"time": 0.0, "kind": ARRIVAL},
            ],
        },
        "output": {"path": "runs", "format": "parquet"},
    }
    return Config.model_validate(data)


def run_mm1(until: float = 100.0) -> State:
    from ..core.engine_event import EventEngine

    cfg = build_mm1_config()
    cfg.engine.until = until
    rng = RNG(cfg.seed)
    state = State(cfg.state.size)
    for name, field in cfg.state.fields.items():
        state.add_field(name, field.dtype, field.init)
    engine = EventEngine(state, start_time=0.0, rng=rng, handle_event_fn=mm1_event_handler)
    for init_event in cfg.engine.initial_events:
        engine.schedule(time=init_event.get("time", 0.0), kind=init_event["kind"], payload=init_event.get("payload"))
    engine.run(until=until, progress=False)
    return state
