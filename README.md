# fast-sim

Vectorised micro and discrete-event simulation with deterministic RNG and batteries-included experiment tooling.

[![CI](https://github.com/mmprotest/fast-sim/actions/workflows/ci.yml/badge.svg)](https://github.com/mmprotest/fast-sim/actions/workflows/ci.yml)
![Python](https://img.shields.io/badge/python-3.10%20|%203.11%20|%203.12-blue)
![License](https://img.shields.io/badge/license-MIT-green)

## 90-second quickstart

> Note on name collisions  
> There is an unrelated project called **fastsim** on PyPI. This package is published as **fast-sim**. Until the first PyPI release is live, use the editable install below.

```bash
python -m venv .venv
source .venv/bin/activate
pip install -e ".[dev,bench,viz]"
fsim info
fsim run --config examples/configs/sir_demo.yaml --steps 50 --seed 123
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
fsim bench --quick
```

Install optional extras to compare with `simpy` and `mesa`. Missing adapters are reported without failing.

### How this differs from SimPy / Mesa
| Aspect | fast-sim | SimPy | Mesa |
|---|---|---|---|
| State model | Vectorised NumPy arrays | Process/yield model | Object-per-agent |
| Determinism | Central RNG with seed, stable outputs | Deterministic when carefully seeded | Deterministic with care |
| Batteries included | CLI, sweeps, metrics, tiny benchmarks | Library focused | Framework focused |
| Footprint | Minimal core deps | Minimal | Heavier (framework) |

### Release status
Targeting v0.1.0. Until PyPI is live, please use the editable install. See `RELEASE_NOTES.md`.

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
