"""Persist simulation results."""
from __future__ import annotations

import json
from pathlib import Path

import pandas as pd

try:  # pragma: no cover - optional
    import pyarrow  # noqa: F401
    _HAVE_PARQUET = True
except Exception:  # pragma: no cover
    _HAVE_PARQUET = False

from .results import ResultSet


def write_results(run_dir: str | Path, metrics_df: pd.DataFrame, state_df: pd.DataFrame | None = None) -> dict[str, Path]:
    run_path = Path(run_dir)
    run_path.mkdir(parents=True, exist_ok=True)
    outputs: dict[str, Path] = {}
    metrics_path = run_path / ("metrics.parquet" if _HAVE_PARQUET else "metrics.csv")
    if _HAVE_PARQUET:
        metrics_df.to_parquet(metrics_path, index=False)
    else:
        metrics_df.to_csv(metrics_path, index=False)
    outputs["metrics"] = metrics_path
    if state_df is not None:
        state_path = run_path / ("state_sample.parquet" if _HAVE_PARQUET else "state_sample.csv")
        if _HAVE_PARQUET:
            state_df.to_parquet(state_path, index=False)
        else:
            state_df.to_csv(state_path, index=False)
        outputs["state"] = state_path
    manifest = run_path / "manifest.json"
    manifest.write_text(json.dumps({k: str(v) for k, v in outputs.items()}, indent=2))
    outputs["manifest"] = manifest
    return outputs


def read_results(path: str | Path) -> ResultSet:
    path = Path(path)
    if path.is_file():
        paths = [path]
    else:
        paths = sorted(path.glob("metrics.*"))
        if not paths:
            paths = sorted(path.rglob("metrics.*"))
    return ResultSet(paths)
