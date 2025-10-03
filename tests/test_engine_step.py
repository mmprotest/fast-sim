from fast_sim.core.engine_step import StepEngine
from fast_sim.core.metrics import Metrics
from fast_sim.core.rng import RNG
from fast_sim.core.state import State
from fast_sim.core.timeline import Timeline


def birth_death_tick(metrics: Metrics):
    def tick(state: State, rng: RNG, t: float) -> None:
        population = state["population"]
        births = int(rng.poisson(lam=2.0))
        deaths = int(min(population[0], rng.poisson(lam=1.0)))
        population[0] = population[0] + births - deaths
        metrics.observe("population", float(population[0]), t)
    return tick


def test_step_engine_runs_to_horizon():
    state = State(1)
    state.add_field("population", int, 10)
    metrics = Metrics()
    timeline = Timeline(t0=0.0, dt=1.0, horizon=10.0)
    engine = StepEngine(state, timeline, RNG(123), birth_death_tick(metrics), metrics=metrics)
    summary = engine.run(progress=False)
    assert summary.steps == 10
    df = metrics.to_frame()
    assert not df.empty
    assert df["value"].min() >= 0
