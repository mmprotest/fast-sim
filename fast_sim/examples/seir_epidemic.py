"""SEIR time-step example."""
from __future__ import annotations

from ..core.rng import RNG
from ..core.state import State
from ..io.config import Config

SUSCEPTIBLE = 0
EXPOSED = 1
INFECTIOUS = 2
RECOVERED = 3


def seir_tick(state: State, rng: RNG, t: float) -> None:
    statuses = state["status"]
    beta = state["beta"][0]
    sigma = state["sigma"][0]
    gamma = state["gamma"][0]
    population = len(statuses)
    infectious_indices = [i for i, status in enumerate(statuses) if status == INFECTIOUS]
    susceptible_indices = [i for i, status in enumerate(statuses) if status == SUSCEPTIBLE]
    exposed_indices = [i for i, status in enumerate(statuses) if status == EXPOSED]

    infection_prob = min(1.0, beta * len(infectious_indices) / max(population, 1))
    if susceptible_indices:
        draws_raw = rng.random(size=len(susceptible_indices))
        draws = draws_raw if isinstance(draws_raw, list) else [draws_raw]
        for idx, draw in zip(susceptible_indices, draws):
            if draw < infection_prob:
                statuses[idx] = EXPOSED

    if exposed_indices:
        draws_raw = rng.random(size=len(exposed_indices))
        draws = draws_raw if isinstance(draws_raw, list) else [draws_raw]
        for idx, draw in zip(exposed_indices, draws):
            if draw < sigma:
                statuses[idx] = INFECTIOUS

    if infectious_indices:
        draws_raw = rng.random(size=len(infectious_indices))
        draws = draws_raw if isinstance(draws_raw, list) else [draws_raw]
        for idx, draw in zip(infectious_indices, draws):
            if draw < gamma:
                statuses[idx] = RECOVERED


def build_seir_config(population: int = 100, beta: float = 0.3, sigma: float = 0.2, gamma: float = 0.1) -> Config:
    data = {
        "seed": 123,
        "state": {
            "size": population,
            "fields": {
                "status": {"dtype": "int64", "init": [SUSCEPTIBLE] * (population - 1) + [INFECTIOUS]},
                "beta": {"dtype": "float64", "init": beta},
                "sigma": {"dtype": "float64", "init": sigma},
                "gamma": {"dtype": "float64", "init": gamma},
            },
        },
        "engine": {
            "type": "step",
            "dt": 1.0,
            "horizon": 60.0,
            "tick": "fast_sim.examples.seir_epidemic:seir_tick",
        },
    }
    return Config.model_validate(data)


def run_seir(days: float = 60.0) -> State:
    from ..core.engine_step import StepEngine
    from ..core.metrics import Metrics
    from ..core.timeline import Timeline

    cfg = build_seir_config()
    cfg.engine.horizon = days
    rng = RNG(cfg.seed)
    state = State(cfg.state.size)
    for name, field in cfg.state.fields.items():
        state.add_field(name, field.dtype, field.init)
    metrics = Metrics()
    timeline = Timeline(t0=0.0, dt=cfg.engine.dt, horizon=cfg.engine.horizon)
    engine = StepEngine(state, timeline, rng, seir_tick, metrics=metrics)
    engine.run(progress=False)
    return state
