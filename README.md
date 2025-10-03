# fast-sim

Fast Sim is a tiny, production-ready framework for building micro/agent-based and
discrete-event simulations in pure Python. It combines a vectorised core,
deterministic random number streams, friendly ergonomics, and batteries-included
experiment tooling so you can focus on modelling instead of infrastructure.

## Why fast-sim?

* **Productive** – build simulations with plain Python functions. No obscure DSLs
  or heavyweight class hierarchies.
* **Deterministic** – every run uses reproducible RNG streams with named child
  generators.
* **Vectorised** – columnar state storage allows fast NumPy-powered updates.
* **Complete** – parameter sweeps, manifests, metrics aggregation, CLI helpers,
  and optional plotting are built-in.
* **Lightweight** – zero heavy dependencies by default. Optional extras (Numba,
  NetworkX, matplotlib, Polars) are lazy imports.

Compared with SimPy or ad-hoc pandas notebooks, Fast Sim emphasises a clean API
for both time-step (Δt) and discrete-event models while keeping the core small
and inspectable.

## Installation

```bash
pip install fast-sim
```

During development you can install in editable mode:

```bash
pip install -e .[numba,networkx,matplotlib]
```

## Quickstart

### Time-step (SEIR epidemic)

```python
from fast_sim import RNG, State, Timeline, StepEngine
from fast_sim.examples.seir_epidemic import seir_tick

state = State(100)
state.add_field("status", int, [0] * 99 + [2])
state.add_field("beta", float, 0.3)
state.add_field("sigma", float, 0.2)
state.add_field("gamma", float, 0.1)

rng = RNG(123)
timeline = Timeline(t0=0.0, dt=1.0, horizon=60.0)
engine = StepEngine(state, timeline, rng, seir_tick)
engine.run(progress=False)
```

### Discrete-event (M/M/1 queue)

```python
from fast_sim import EventEngine, RNG, State
from fast_sim.examples.mm1_queue import mm1_event_handler, ARRIVAL

state = State(1)
state.add_field("queue_length", int, 0)
state.add_field("busy", int, 0)
state.add_field("arrivals", int, 0)
state.add_field("departures", int, 0)
state.add_field("arrival_rate", float, 0.8)
state.add_field("service_rate", float, 1.0)

engine = EventEngine(state, start_time=0.0, rng=RNG(42), handle_event_fn=mm1_event_handler)
engine.schedule(time=0.0, kind=ARRIVAL)
engine.run(until=100.0, progress=False)
```

### CLI helpers

```bash
fsim init --example mm1 --out sim/
fsim run sim/config.yaml --out runs/
fsim sweep sim/config.yaml --out runs/ --runs 3
fsim summarize runs/ --metric population
```

## Reproducibility

Randomness is handled by `fast_sim.core.RNG`, a deterministic wrapper over
Python's ``random.Random`` with named spawning. Call `rng.spawn("foo")`
anywhere to obtain an independent, repeatable child stream. Experiments use the
same mechanism to ensure sweeps and repeated runs never collide.

## Engines

Fast Sim ships two complementary engines:

```
Time-step:           Discrete-event:
┌──────────────┐     ┌──────────────┐
│ Timeline(dt) │     │ EventQueue   │
└──────┬───────┘     └──────┬───────┘
       ▼                    ▼
 State + tick_fn      State + handler
       ▼                    ▼
   Metrics/Policies   Metrics/Policies
```

* `StepEngine` advances the simulation with a fixed Δt, applying policies and a
  user-supplied `tick_fn(state, rng, t)` each step.
* `EventEngine` pops events ordered by time/priority. The handler receives the
  current event and can schedule future events.

Both engines integrate with policies, tracing, metrics collection, and optional
progress bars via Rich.

## Experiments & parameter sweeps

Describe simulations in YAML/TOML using lightweight dataclass models. Example snippet:

```yaml
seed: 5
state:
  size: 1
  fields:
    counter:
      dtype: int64
      init: 0
engine:
  type: step
  dt: 1.0
  horizon: 5.0
  tick: tests.test_experiment_sweeps:tick_fn
sweep:
  engine.horizon: [5.0, 7.0]
```

Then execute:

```python
from fast_sim.io.config import load_config
from fast_sim.io.experiment import Experiment

config = load_config("config.yaml")
exp = Experiment(config, sweep=config.sweep, runs=3)
summary = exp.execute("runs/")
print(summary.result_set().summary())
```

Each run writes:

* `metrics.parquet` (or CSV fallback)
* `state_sample.parquet`
* `manifest.json` with parameters, seeds, and metadata

`fast_sim.io.results.ResultSet` makes concatenation and aggregation easy.

## Performance tips

* Keep large arrays in `State` and favour vectorised NumPy operations.
* Spawn RNG streams for independent subsystems (agents, policies) to minimise
  cache effects.
* Optional extras:
  * `numba` – jit-compile heavy kernels.
  * `networkx` – richer graph spaces.
  * `matplotlib` – quick plots via `fast_sim.viz.quickplots`.
  * `polars` – fast IO in `fast_sim.io.datasets` if installed.

Baseline targets: simple Δt loops can exceed one million agent-ticks per second
on a modern laptop without JIT compilation.

## Limitations & roadmap

* No built-in distributed execution – scale-out strategies (Ray/Dask) are left
  to the user.
* Visualisation is intentionally minimal; integrate with Plotly/Bokeh for richer
  dashboards.
* Event tracing is lightweight JSONL; heavy telemetry belongs in external tools.

## Contributing

1. `pip install -e .[numba,networkx,matplotlib]`
2. `pre-commit install`
3. Run `ruff`, `black`, `mypy`, and `pytest` locally before opening a PR.

Fast Sim is released under the MIT license.
