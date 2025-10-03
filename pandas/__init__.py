"""Tiny pandas-compatible subset for fast-sim tests."""
from __future__ import annotations

import csv
import math
import statistics
from collections import defaultdict
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable, Iterable, Iterator, Mapping, Sequence

Number = int | float


def _is_numeric(value: Any) -> bool:
    return isinstance(value, (int, float))


class Series(list):
    def dropna(self) -> "Series":
        return Series([x for x in self if x is not None and not (isinstance(x, float) and math.isnan(x))])

    def to_numpy(self) -> list[Any]:
        return list(self)

    @property
    def values(self) -> list[Any]:
        return self.to_numpy()

    def mean(self) -> float:
        arr = [x for x in self if _is_numeric(x)]
        return float(sum(arr) / len(arr)) if arr else float("nan")

    def std(self) -> float:
        arr = [x for x in self if _is_numeric(x)]
        return float(statistics.pstdev(arr)) if len(arr) > 1 else 0.0

    def sum(self) -> float:
        arr = [x for x in self if _is_numeric(x)]
        return float(sum(arr))

    def min(self) -> float:
        arr = [x for x in self if _is_numeric(x)]
        return float(min(arr)) if arr else float("nan")

    def max(self) -> float:
        arr = [x for x in self if _is_numeric(x)]
        return float(max(arr)) if arr else float("nan")


class DataFrame:
    def __init__(self, data: Any | None = None, columns: Sequence[str] | None = None) -> None:
        if data is None:
            self._rows: list[dict[str, Any]] = []
        elif isinstance(data, Mapping):
            cols = list(data.keys()) if columns is None else list(columns)
            values = [list(data[col]) for col in cols]
            length = len(values[0]) if values else 0
            self._rows = [
                {col: values[idx][row] for idx, col in enumerate(cols)} for row in range(length)
            ]
        elif isinstance(data, list):
            if not data:
                self._rows = []
            elif isinstance(data[0], Mapping):
                self._rows = [dict(row) for row in data]
            else:
                raise TypeError("Unsupported data format for DataFrame")
        else:
            raise TypeError("Unsupported data format for DataFrame")
        self._columns = columns or (list(data.keys()) if isinstance(data, Mapping) else (list(self._rows[0].keys()) if self._rows else []))

    @classmethod
    def from_records(cls, records: Iterable[Mapping[str, Any]]) -> "DataFrame":
        return cls(list(records))

    @property
    def columns(self) -> list[str]:
        return list({key for row in self._rows for key in row.keys()})

    @property
    def empty(self) -> bool:
        return len(self._rows) == 0

    def copy(self) -> "DataFrame":
        return DataFrame(list(self._rows))

    def to_dicts(self) -> list[dict[str, Any]]:
        return [dict(row) for row in self._rows]

    def to_csv(self, path: str | Path, index: bool = False) -> None:
        path = Path(path)
        rows = self.to_dicts()
        cols = self.columns
        with path.open("w", newline="") as fh:
            writer = csv.DictWriter(fh, fieldnames=cols)
            writer.writeheader()
            for row in rows:
                writer.writerow({col: row.get(col, "") for col in cols})

    def head(self, n: int = 5) -> "DataFrame":
        return DataFrame(self._rows[:n])

    def sample(self, n: int, random_state: int | None = None) -> "DataFrame":
        if not self._rows:
            return DataFrame([])
        rng = random.Random(random_state)
        indices = rng.sample(range(len(self._rows)), k=n)
        return DataFrame([self._rows[i] for i in indices])

    def reset_index(self, drop: bool = True) -> "DataFrame":
        return self.copy()

    def __len__(self) -> int:
        return len(self._rows)

    def __getitem__(self, key: str | list[str]) -> Series | "DataFrame":
        if isinstance(key, list):
            return DataFrame([{col: row.get(col) for col in key} for row in self._rows])
        return Series([row.get(key) for row in self._rows])

    def __setitem__(self, key: str, value: Iterable[Any]) -> None:
        for row, val in zip(self._rows, value):
            row[key] = val

    def __iter__(self) -> Iterator[dict[str, Any]]:
        return iter(self._rows)

    @property
    def values(self) -> list[list[Any]]:
        return [[row.get(col) for col in self.columns] for row in self._rows]

    def select_dtypes(self, include: str) -> "DataFrame":
        if include != "number":
            return DataFrame([])
        numeric_cols = [col for col in self.columns if self._rows and _is_numeric(next((row.get(col) for row in self._rows if row.get(col) is not None), 0))]
        return DataFrame([{col: row.get(col) for col in numeric_cols} for row in self._rows])

    def agg(self, funcs: Sequence[str]) -> "DataFrame":
        rows: list[dict[str, Any]] = []
        numeric_cols = self.select_dtypes("number").columns
        if not numeric_cols:
            return DataFrame([])
        row: dict[str, Any] = {}
        for func in funcs:
            for col in numeric_cols:
                series = [row_.get(col) for row_ in self._rows if _is_numeric(row_.get(col))]
                if not series:
                    continue
                value = _apply_func(series, func)
                row[f"{col}_{func}"] = value
        rows.append(row)
        return DataFrame(rows)

    def groupby(self, by: Sequence[str] | str) -> "GroupBy":
        return GroupBy(self, [by] if isinstance(by, str) else list(by))

    def to_parquet(self, path: str | Path, index: bool = False) -> None:  # pragma: no cover - compatibility stub
        raise RuntimeError("Parquet support unavailable in minimal pandas stub")


class GroupBy:
    def __init__(self, df: DataFrame, by: list[str], columns: list[str] | None = None) -> None:
        self.df = df
        self.by = by
        self.columns = columns

    def __getitem__(self, cols: Sequence[str]) -> "GroupBy":
        return GroupBy(self.df, self.by, list(cols))

    def agg(self, funcs: Sequence[str] | Mapping[str, Sequence[str]]) -> DataFrame:
        if isinstance(funcs, Mapping):
            cols_map = {col: list(fns) for col, fns in funcs.items()}
        else:
            target_cols = self.columns or self.df.select_dtypes("number").columns
            cols_map = {col: list(funcs) for col in target_cols}
        grouped: dict[tuple[Any, ...], list[dict[str, Any]]] = defaultdict(list)
        for row in self.df:
            key = tuple(row.get(col) for col in self.by)
            grouped[key].append(row)
        result_rows: list[dict[str, Any]] = []
        for key, rows in grouped.items():
            out: dict[str, Any] = {}
            for idx, col in enumerate(self.by):
                out[col] = key[idx]
            for col, funcs_list in cols_map.items():
                series = [row.get(col) for row in rows if _is_numeric(row.get(col))]
                for func in funcs_list:
                    out[f"{col}_{func}"] = _apply_func(series, func)
            result_rows.append(out)
        return DataFrame(result_rows)


def concat(frames: Sequence[DataFrame], ignore_index: bool = True) -> DataFrame:
    rows: list[dict[str, Any]] = []
    for frame in frames:
        rows.extend(frame.to_dicts())
    return DataFrame(rows)


def read_csv(path: str | Path) -> DataFrame:
    path = Path(path)
    with path.open() as fh:
        reader = csv.DictReader(fh)
        rows = [dict(row) for row in reader]
    for row in rows:
        for key, value in row.items():
            if value == "":
                row[key] = None
            else:
                try:
                    if "." in value:
                        row[key] = float(value)
                    else:
                        row[key] = int(value)
                except ValueError:
                    pass
    return DataFrame(rows)


def read_parquet(path: str | Path) -> DataFrame:  # pragma: no cover - compatibility stub
    raise RuntimeError("Parquet support unavailable in minimal pandas stub")


def _apply_func(values: Sequence[Number], func: str) -> float:
    if not values:
        return float("nan")
    if func == "mean":
        return float(sum(values) / len(values))
    if func == "std":
        return float(statistics.pstdev(values)) if len(values) > 1 else 0.0
    if func == "min":
        return float(min(values))
    if func == "max":
        return float(max(values))
    if func == "median":
        return float(statistics.median(values))
    raise ValueError(f"Unsupported aggregate {func}")


__all__ = ["DataFrame", "Series", "concat", "read_csv", "read_parquet"]
