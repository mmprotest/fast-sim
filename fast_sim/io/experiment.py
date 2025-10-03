"""Experiment orchestration utilities."""
from __future__ import annotations

import itertools
import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, Iterable

import pandas as pd

from rich.progress import Progress

from ..core.engine_event import EventEngine
from ..core.engine_step import StepEngine
from ..core.metrics import Metrics
from ..core.rng import RNG
from ..core.state import State
from ..core.timeline import Timeline
from .config import Config, EventEngineConfig, StepEngineConfig, import_callable
from .datasets import write_results
from .results import ResultSet


@dataclass
class ExperimentRun:
    params: dict[str, Any]
    run_path: Path
    metrics_path: Path


@dataclass
class ExperimentSummary:
    runs: list[ExperimentRun] = field(default_factory=list)

    def result_set(self) -> ResultSet:
        return ResultSet([run.metrics_path for run in self.runs])


class Experiment:
    """Execute parameter sweeps over configurations."""

    def __init__(
        self,
        base_config: Config,
        sweep: dict[str, Iterable[Any]] | None = None,
        runs: int = 1,
        seed: int | None = None,
        max_workers: int = 1,
        backend: str = "process",
    ) -> None:
        self.base_config = base_config
        self.sweep = sweep or {}
        self.runs = runs
        self.seed = seed
        self.max_workers = max_workers
        self.backend = backend

    def execute(self, out_dir: str | Path, progress: bool = True) -> ExperimentSummary:
        out_path = Path(out_dir)
        out_path.mkdir(parents=True, exist_ok=True)
        base_rng = RNG(self.seed or self.base_config.seed)
        summary = ExperimentSummary()
        sweep_keys = list(self.sweep.keys())
        sweep_values = [list(v) for v in self.sweep.values()]
        scenarios = list(itertools.product(*sweep_values)) if sweep_values else [()]
        progress_bar: Progress | None = None
        task_id = None
        total_runs = len(scenarios) * self.runs
        if progress:
            progress_bar = Progress(transient=True)
            progress_bar.__enter__()
            task_id = progress_bar.add_task("experiment", total=total_runs)
        for combo in scenarios:
            params = dict(zip(sweep_keys, combo))
            scenario_name = self._scenario_name(params)
            for rep in range(self.runs):
                run_rng = base_rng.spawn(f"run:{scenario_name}:{rep}")
                cfg = self._apply_params(self.base_config, params)
                result = self._run_single(cfg, run_rng)
                run_dir = out_path / f"{scenario_name}_run{rep}"
                outputs = write_results(run_dir, result["metrics"], result["state_sample"])
                manifest_path = run_dir / "manifest.json"
                manifest_path.write_text(
                    json.dumps(
                        {
                            "params": params,
                            "scenario": scenario_name,
                            "summary": {
                                "records": len(result["metrics"]),
                            },
                        },
                        indent=2,
                    )
                )
                run = ExperimentRun(params=params, run_path=run_dir, metrics_path=outputs["metrics"])
                summary.runs.append(run)
                if progress_bar is not None and task_id is not None:
                    progress_bar.update(task_id, advance=1)
        if progress_bar is not None:
            progress_bar.__exit__(None, None, None)
        return summary

    def _scenario_name(self, params: dict[str, Any]) -> str:
        if not params:
            return "base"
        parts = [f"{k}-{v}" for k, v in params.items()]
        return "_".join(parts)

    def _apply_params(self, cfg: Config, params: dict[str, Any]) -> Config:
        data = cfg.model_dump(mode="python")
        for key, value in params.items():
            target = data
            parts = key.split(".")
            for part in parts[:-1]:
                target = target.setdefault(part, {})
            target[parts[-1]] = value
        return Config.model_validate(data)

    def _build_state(self, config: Config, rng: RNG) -> State:
        state_cfg = config.state
        state = State(state_cfg.size)
        for name, field_cfg in state_cfg.fields.items():
            init = field_cfg.init
            values: Any
            if isinstance(init, str) and ("." in init or ":" in init):
                initializer = import_callable(init)
                values = initializer(rng, state_cfg.size)
            else:
                values = init
            state.add_field(name, field_cfg.dtype, values)
        return state

    def _build_policies(self, config: Config) -> list:
        return [policy.build() for policy in config.policies]

    def _run_single(self, config: Config, run_rng: RNG) -> Dict[str, pd.DataFrame]:
        state = self._build_state(config, run_rng)
        policies = self._build_policies(config)
        metrics = Metrics()
        if isinstance(config.engine, StepEngineConfig):
            tick = import_callable(config.engine.tick)
            timeline = Timeline(t0=0.0, dt=config.engine.dt, horizon=config.engine.horizon)
            engine = StepEngine(state, timeline, run_rng, tick, metrics=metrics, policies=policies)
            summary = engine.run(progress=False)
        else:
            handler = import_callable(config.engine.handler)
            engine = EventEngine(state, start_time=0.0, rng=run_rng, handle_event_fn=handler, metrics=metrics, policies=policies)
            for event_def in config.engine.initial_events:
                engine.schedule(
                    time=event_def.get("time", 0.0),
                    kind=event_def["kind"],
                    payload=event_def.get("payload"),
                    target_id=event_def.get("target_id"),
                    priority=event_def.get("priority", 0),
                )
            summary = engine.run(until=config.engine.until, progress=False)
        metrics_df = metrics.to_frame()
        if metrics_df.empty:
            metrics_df = pd.DataFrame([{"t": summary.end_time if hasattr(summary, "end_time") else 0.0}])
        state_sample = state.as_dataframe(sample=min(5, state.size))
        return {"metrics": metrics_df, "state_sample": state_sample}
