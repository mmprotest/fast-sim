# Fast Sim Examples

The `examples/` directory contains runnable scripts that showcase the most common workflows for Fast Sim users. Each script can be executed with plain Python and demonstrates how to configure state, run the engines, and capture simple metrics for later analysis.

## Available examples

| File | Scenario | Highlights |
| --- | --- | --- |
| [`seir_epidemic.py`](seir_epidemic.py) | Compartmental epidemic model | Uses `StepEngine`, tracks compartment counts, reports infection peak. |
| [`mm1_queue.py`](mm1_queue.py) | M/M/1 queue with exponential arrivals/services | Uses `EventEngine`, records utilisation and throughput. |
| [`traffic_cellular_automata.py`](traffic_cellular_automata.py) | Single-lane traffic cellular automaton | Uses `StepEngine`, measures average speed and density. |

## Running an example

```bash
python examples/seir_epidemic.py
python examples/mm1_queue.py
python examples/traffic_cellular_automata.py
```

Each script exposes a `simulate_*` function that can be imported into notebooks or test suites when you want to customise parameters or embed the simulations in larger experiments.

All examples rely only on the public Fast Sim API and therefore double as templates for building your own models.
