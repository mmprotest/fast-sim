"""Command line interface for fast-sim."""
from __future__ import annotations

from pathlib import Path
from typing import Optional

import typer
from rich.console import Console

from ruamel.yaml import YAML

from .examples import build_mm1_config, build_seir_config, build_traffic_config
from .io.config import Config, load_config
from .io.datasets import read_results
from .io.experiment import Experiment

console = Console()
app = typer.Typer(help="Fast simulations with minimal boilerplate.")


def _write_example(out: Path, config: Config, script_path: Path) -> None:
    out.mkdir(parents=True, exist_ok=True)
    config_path = out / "config.yaml"
    yaml = YAML()
    with config_path.open("w") as fh:
        yaml.dump(config.model_dump(mode="python"), fh)
    script_target = out / script_path.name
    script_target.write_text(script_path.read_text())
    console.print(f"Wrote example to {out}")


@app.command()
def init(example: str = typer.Option(..., help="Example name: mm1|seir|traffic"), out: Path = typer.Option(Path("sim"))) -> None:
    example = example.lower()
    base = Path(__file__).resolve().parent
    if example == "mm1":
        cfg = build_mm1_config()
        script = base / "examples" / "mm1_queue.py"
    elif example == "seir":
        cfg = build_seir_config()
        script = base / "examples" / "seir_epidemic.py"
    elif example == "traffic":
        cfg = build_traffic_config()
        script = base / "examples" / "traffic_ca.py"
    else:
        raise typer.BadParameter("Unknown example")
    _write_example(out, cfg, script)


def _run_experiment(cfg: Config, out: Path, sweep: Optional[dict[str, list]] = None, runs: int = 1) -> None:
    experiment = Experiment(cfg, sweep=sweep, runs=runs, seed=cfg.seed)
    summary = experiment.execute(out)
    console.print(f"Completed {len(summary.runs)} runs; results in {out}")


@app.command()
def run(config: Path, out: Path = typer.Option(Path("runs")), runs: int = typer.Option(1)) -> None:
    cfg = load_config(config)
    _run_experiment(cfg, out, runs=runs)


@app.command()
def sweep(config: Path, out: Path = typer.Option(Path("runs")), runs: int = typer.Option(1)) -> None:
    cfg = load_config(config)
    if not cfg.sweep:
        raise typer.BadParameter("Config missing sweep section")
    _run_experiment(cfg, out, sweep=cfg.sweep, runs=runs)


@app.command()
def summarize(path: Path, metric: str | None = typer.Option(None), by: str | None = typer.Option(None)) -> None:
    rs = read_results(path)
    df = rs.concat()
    if df.empty:
        console.print("No results found")
        return
    if metric and "metric" in df.columns:
        df = df[df["metric"] == metric]
    if by:
        summary = df.groupby(by).agg({"value": ["mean", "std"]})
        console.print(summary)
        return
    console.print(df.head())


@app.command()
def plot(path: Path, metric: str, out: Path = typer.Option(Path("plot.png"))) -> None:
    from .viz.quickplots import plot_series
    import matplotlib.pyplot as plt

    rs = read_results(path)
    df = rs.concat()
    if df.empty:
        console.print("No data to plot")
        return
    plt.figure()
    plot_series(df, [metric])
    plt.savefig(out)
    console.print(f"Saved plot to {out}")
