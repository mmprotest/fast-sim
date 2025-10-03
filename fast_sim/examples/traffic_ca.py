"""Traffic cellular automaton example."""
from __future__ import annotations

from ..core.rng import RNG
from ..core.state import State
from ..io.config import Config


def traffic_tick(state: State, rng: RNG, t: float) -> None:
    road = state["road"]
    velocity = state["velocity"]
    vmax = int(state["vmax"][0])
    slow_prob = state["slow_prob"][0]
    length = len(road)
    new_velocity = list(velocity)
    car_positions = [idx for idx, value in enumerate(road) if value >= 0]
    for pos in car_positions:
        v = min(velocity[pos] + 1, vmax)
        gap = 1
        while gap <= v and road[(pos + gap) % length] < 0:
            gap += 1
        v = min(v, gap - 1)
        slow_draw = rng.random()
        slow_value = slow_draw if isinstance(slow_draw, float) else slow_draw[0]
        if v > 0 and slow_value < slow_prob:
            v -= 1
        new_velocity[pos] = v
    new_road = [-1 for _ in range(length)]
    for pos in car_positions:
        v = new_velocity[pos]
        new_pos = (pos + v) % length
        new_road[new_pos] = 1
    for idx in range(length):
        road[idx] = new_road[idx]
        velocity[idx] = new_velocity[idx]


def build_traffic_config(length: int = 50, density: float = 0.3, vmax: int = 5, slow_prob: float = 0.2) -> Config:
    cars = int(length * density)
    road = [-1 for _ in range(length)]
    for i in range(cars):
        road[i] = 1
    import random

    random.Random(0).shuffle(road)
    velocity = [0 for _ in range(length)]
    data = {
        "seed": 999,
        "state": {
            "size": length,
            "fields": {
                "road": {"dtype": "int64", "init": road},
                "velocity": {"dtype": "int64", "init": velocity},
                "vmax": {"dtype": "int64", "init": vmax},
                "slow_prob": {"dtype": "float64", "init": slow_prob},
            },
        },
        "engine": {
            "type": "step",
            "dt": 1.0,
            "horizon": 60.0,
            "tick": "fast_sim.examples.traffic_ca:traffic_tick",
        },
    }
    return Config.model_validate(data)


def run_traffic(steps: float = 60.0) -> State:
    from ..core.engine_step import StepEngine
    from ..core.metrics import Metrics
    from ..core.timeline import Timeline

    cfg = build_traffic_config()
    cfg.engine.horizon = steps
    rng = RNG(cfg.seed)
    state = State(cfg.state.size)
    for name, field in cfg.state.fields.items():
        state.add_field(name, field.dtype, field.init)
    metrics = Metrics()
    timeline = Timeline(t0=0.0, dt=cfg.engine.dt, horizon=cfg.engine.horizon)
    engine = StepEngine(state, timeline, rng, traffic_tick, metrics=metrics)
    engine.run(progress=False)
    return state
