"""Benchmark runner for fast_sim."""
from __future__ import annotations

import importlib
import time
from typing import Any, List

import numpy as np

from fast_sim import Simulation
from fast_sim.agents import queue_step, sir_step
from fast_sim.random import set_seed

from .scenarios import SCENARIOS, Scenario


def _run_fast_sim(scenario: Scenario, quick: bool) -> dict[str, Any]:
    cfg = scenario.config.copy(deep=True)
    if quick:
        cfg.steps = max(10, cfg.steps // 5)
        cfg.n_agents = max(100, cfg.n_agents // 10)
    sim = Simulation.from_config(cfg, agent_step=scenario.step_fn)
    if scenario.step_fn is sir_step:
        agents = np.zeros((cfg.n_agents, 1), dtype=float)
        agents[: int(cfg.params.get("initial_infected", 1)), 0] = 1
        sim.state["agents"] = agents
    elif scenario.step_fn is queue_step:
        agents = np.zeros((cfg.n_agents, 2), dtype=float)
        sim.state["agents"] = agents
    start = time.perf_counter()
    sim.run(cfg.steps)
    duration = time.perf_counter() - start
    throughput = cfg.steps * cfg.n_agents / duration if duration > 0 else float("inf")
    return {
        "Engine": "fast-sim",
        "Scenario": scenario.name,
        "Agents": cfg.n_agents,
        "Steps": cfg.steps,
        "Seconds": duration,
        "Steps/s": throughput,
    }


def _run_adapter(name: str, module_name: str, quick: bool) -> List[dict[str, Any]]:
    if importlib.util.find_spec(module_name) is None:
        return [
            {
                "Engine": name,
                "Scenario": "-",
                "Agents": "-",
                "Steps": "-",
                "Seconds": float("nan"),
                "Steps/s": "adapter not available",
            }
        ]
    module = importlib.import_module(module_name)
    results: List[dict[str, Any]] = []
    for scenario in SCENARIOS:
        cfg = scenario.config.copy(deep=True)
        if quick:
            cfg.steps = max(10, cfg.steps // 5)
            cfg.n_agents = max(100, cfg.n_agents // 10)
        start = time.perf_counter()
        if hasattr(module, "run_benchmark"):
            module.run_benchmark(cfg.n_agents, cfg.steps)
        else:
            time.sleep(0.001)
        duration = time.perf_counter() - start
        throughput = cfg.steps * cfg.n_agents / duration if duration > 0 else float("inf")
        results.append(
            {
                "Engine": name,
                "Scenario": scenario.name,
                "Agents": cfg.n_agents,
                "Steps": cfg.steps,
                "Seconds": duration,
                "Steps/s": throughput,
            }
        )
    return results


def main(quick: bool = False, seed: int | None = None) -> None:
    if seed is not None:
        set_seed(seed)
    rows: List[dict[str, Any]] = []
    for scenario in SCENARIOS:
        rows.append(_run_fast_sim(scenario, quick))
    rows.extend(_run_adapter("simpy", "simpy", quick))
    rows.extend(_run_adapter("mesa", "mesa", quick))
    _print_markdown_table(rows)


def _print_markdown_table(rows: List[dict[str, Any]]) -> None:
    if not rows:
        return
    headers = list(rows[0].keys())
    print("| " + " | ".join(headers) + " |")
    print("| " + " | ".join(["---"] * len(headers)) + " |")
    for row in rows:
        formatted = [f"{row[h]:.4f}" if isinstance(row[h], float) else str(row[h]) for h in headers]
        print("| " + " | ".join(formatted) + " |")


if __name__ == "__main__":
    main()
