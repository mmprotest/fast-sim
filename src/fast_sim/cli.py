"""Command line interface for fast_sim."""
from __future__ import annotations

import importlib
import json
from pathlib import Path
from typing import Any, Dict, Optional

import numpy as np
import typer

from . import Simulation, __version__, load_config
from .agents import queue_step, sir_step
from .config import SimConfig
from .random import set_seed

__all__ = ["app"]

app = typer.Typer(help="Vectorised micro-simulation toolkit")


def _maybe_rich() -> Optional[Any]:
    if importlib.util.find_spec("rich") is None:
        return None
    return importlib.import_module("rich")


def _print_table(rows: list[Dict[str, Any]]) -> None:
    if not rows:
        typer.echo("No metrics recorded.")
        return
    rich = _maybe_rich()
    if rich:
        table = rich.table.Table(title="fast-sim metrics")
        for column in rows[0].keys():
            table.add_column(column)
        for row in rows:
            table.add_row(*(str(row[col]) for col in row.keys()))
        rich.console.Console().print(table)
    else:
        header = " | ".join(rows[0].keys())
        typer.echo(header)
        for row in rows:
            typer.echo(" | ".join(str(value) for value in row.values()))


def _format_metrics(metrics: Dict[str, np.ndarray]) -> list[Dict[str, Any]]:
    rows: list[Dict[str, Any]] = []
    for name, values in metrics.items():
        if values.size == 0:
            continue
        rows.append({
            "metric": name,
            "last": f"{values[-1]:.4f}",
            "mean": f"{values.mean():.4f}",
        })
    return rows


@app.command()
def info() -> None:
    """Display package information."""

    extras = []
    for extra in ("simpy", "mesa", "rich", "matplotlib", "pyyaml"):
        extras.append(f"{extra}:{'yes' if importlib.util.find_spec(extra) else 'no'}")
    typer.echo(json.dumps({"version": __version__, "extras": extras}, indent=2))


def _sir_metrics() -> Dict[str, Any]:
    return {
        "S": lambda state: float(np.sum(state["agents"][:, 0] == 0)),
        "I": lambda state: float(np.sum(state["agents"][:, 0] == 1)),
        "R": lambda state: float(np.sum(state["agents"][:, 0] == 2)),
    }


def _queue_metrics() -> Dict[str, Any]:
    return {
        "queue_length": lambda state: float(state["agents"][:, 0].sum()),
        "mean_wait": lambda state: float(state["agents"][:, 1].mean()),
    }


def _build_sim(cfg: SimConfig) -> Simulation:
    model = cfg.params.get("model", "sir")
    updater = sir_step if model == "sir" else queue_step
    sim = Simulation.from_config(cfg, agent_step=updater)
    if model == "sir":
        agents = np.zeros((cfg.n_agents, 1), dtype=float)
        initial_infected = min(int(cfg.params.get("initial_infected", 1)), cfg.n_agents)
        initial_recovered = min(int(cfg.params.get("initial_recovered", 0)), cfg.n_agents - initial_infected)
        agents[:initial_infected, 0] = 1
        agents[initial_infected : initial_infected + initial_recovered, 0] = 2
        sim.state["agents"] = agents
        for name, extractor in _sir_metrics().items():
            sim.register_metric(name, extractor)
    else:
        agents = np.zeros((cfg.n_agents, 2), dtype=float)
        sim.state["agents"] = agents
        for name, extractor in _queue_metrics().items():
            sim.register_metric(name, extractor)
    return sim


@app.command()
def run(
    config: Path = typer.Option(..., exists=True, readable=True, help="Path to YAML config."),
    steps: Optional[int] = typer.Option(None, help="Override number of steps to run."),
    seed: Optional[int] = typer.Option(None, help="Override RNG seed."),
    out: Optional[Path] = typer.Option(None, help="Optional path to save metrics as NPZ."),
) -> None:
    """Run a simulation from a YAML configuration."""

    cfg = load_config(config)
    if seed is not None:
        cfg.seed = seed
    if steps is not None:
        cfg.steps = steps
    cfg.apply_seed()
    sim = _build_sim(cfg)
    metrics = sim.run(cfg.steps)
    rows = _format_metrics(metrics)
    _print_table(rows)
    final_state = {k: v.tolist() if isinstance(v, np.ndarray) else v for k, v in sim.state.items()}
    typer.echo(json.dumps({"final_state": final_state}, indent=2))
    if out:
        np.savez(out, **metrics)
        typer.echo(f"Saved metrics to {out}")


def _load_benchmarks():
    try:
        return importlib.import_module("fast_sim.benchmarks.runner")
    except ModuleNotFoundError:  # pragma: no cover - fallback for editable installs
        return importlib.import_module("benchmarks.runner")


@app.command()
def bench(
    quick: bool = typer.Option(False, "--quick", help="Run a shorter benchmark suite."),
    seed: Optional[int] = typer.Option(None, help="Seed for deterministic runs."),
) -> None:
    """Execute the benchmark suite."""

    if seed is not None:
        set_seed(seed)
    runner = _load_benchmarks()
    runner.main(quick=quick)


if __name__ == "__main__":
    app()
