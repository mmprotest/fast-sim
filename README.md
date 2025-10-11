# fast-sim

Vectorised micro and discrete-event simulation with deterministic RNG and batteries-included experiment tooling.

[![CI](https://github.com/simonv3/fast-sim/actions/workflows/ci.yml/badge.svg)](https://github.com/simonv3/fast-sim/actions/workflows/ci.yml)
[![PyPI](https://img.shields.io/pypi/v/fast-sim.svg?label=PyPI)](https://pypi.org/project/fast-sim/)
![Python](https://img.shields.io/badge/python-3.10%2B-blue.svg)
![License](https://img.shields.io/badge/license-MIT-green.svg)

## 90-second quickstart

```bash
python -m venv .venv
source .venv/bin/activate
pip install -e '.[dev,bench]'
fastsim info
fastsim run --config examples/configs/sir_demo.yaml --steps 50 --seed 123
```

Expected first lines of output:

```
{
  "version": "0.1.0",
  "extras": [
    "simpy:no",
    "mesa:no",
    "rich:no",
    "typer:yes",
    "pyyaml:yes"
  ]
}
metric | last | mean
{"final_state": {"agents": [[0.0], ...]}}
```

## Minimal API example

```python
from fast_sim import Simulation, SimConfig
from fast_sim.agents import sir_step
import numpy as np

cfg = SimConfig(n_agents=100, steps=30, params={"model": "sir", "beta": 0.2, "gamma": 0.05, "initial_infected": 4})
sim = Simulation.from_config(cfg, agent_step=sir_step)
agents = np.zeros((cfg.n_agents, 1), dtype=float)
agents[:4, 0] = 1
sim.state["agents"] = agents
sim.register_metric("S", lambda state: float(np.sum(state["agents"][:, 0] == 0)))
sim.register_metric("I", lambda state: float(np.sum(state["agents"][:, 0] == 1)))
sim.register_metric("R", lambda state: float(np.sum(state["agents"][:, 0] == 2)))
metrics = sim.run(cfg.steps)
print(metrics["I"].max())
```

## Benchmarks

Run the benchmark harness (fast, deterministic):

```bash
fastsim bench --quick
```

Install optional extras to compare with `simpy` and `mesa`. Missing adapters are reported without failing.

## Roadmap

- [x] Deterministic RNG and vectorised core loop
- [x] CLI with run/info/bench commands
- [x] SIR and traffic queue examples
- [ ] Extended event scheduling API
- [ ] Distributed multi-process execution
- [ ] Additional domain-specific adapters

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md) for environment setup, coding standards, and release instructions.

## License

fast-sim is released under the [MIT License](LICENSE).

## Security

Please review [SECURITY.md](SECURITY.md) for responsible disclosure guidance.
