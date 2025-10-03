"""Aggregating run outputs."""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, Sequence

import pandas as pd

try:  # pragma: no cover - optional
    import pyarrow  # noqa: F401
    _HAVE_PARQUET = True
except Exception:  # pragma: no cover
    _HAVE_PARQUET = False


def _read(path: Path) -> pd.DataFrame:
    if path.suffix == ".parquet" and _HAVE_PARQUET:
        return pd.read_parquet(path)
    return pd.read_csv(path)


@dataclass
class ResultSet:
    paths: Sequence[Path]

    def concat(self) -> pd.DataFrame:
        frames = [_read(Path(p)) for p in self.paths]
        if not frames:
            return pd.DataFrame()
        return pd.concat(frames, ignore_index=True)

    def summary(self, groupby: Iterable[str] | None = None) -> pd.DataFrame:
        df = self.concat()
        if df.empty:
            return df
        group_cols = list(groupby or [])
        if not group_cols:
            agg = df.agg(["mean", "median", "min", "max"])
            return agg
        numeric_cols = df.select_dtypes("number").columns
        grouped = df.groupby(group_cols)[numeric_cols]
        summary = grouped.agg(["mean", "std"])
        return summary.reset_index()

    def __len__(self) -> int:
        return len(self.paths)
