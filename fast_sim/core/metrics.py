"""Metric collection utilities."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Iterable

from statistics import mean
from pandas import DataFrame


@dataclass
class Metrics:
    """Collect counters and time series during simulation runs."""

    counters: dict[str, float] = field(default_factory=dict)
    series: dict[str, list[tuple[float, float]]] = field(default_factory=dict)

    def inc(self, name: str, x: float = 1.0) -> None:
        self.counters[name] = self.counters.get(name, 0.0) + x

    def observe(self, name: str, value: float, t: float) -> None:
        self.series.setdefault(name, []).append((t, value))

    def rate(self, name: str, window: float) -> float:
        data = self.series.get(name)
        if not data:
            return 0.0
        latest_t = data[-1][0]
        acc = [value for t, value in data if latest_t - t <= window]
        return float(mean(acc)) if acc else 0.0

    def snapshot(self, t: float) -> DataFrame:
        rows: list[dict[str, float]] = []
        row: dict[str, float] = {f"counter_{k}": v for k, v in self.counters.items()}
        for name, entries in self.series.items():
            if not entries:
                continue
            row[f"series_{name}"] = entries[-1][1]
        row["t"] = t
        rows.append(row)
        return DataFrame(rows)

    def to_frame(self) -> DataFrame:
        records: list[dict[str, float]] = []
        for name, entries in self.series.items():
            for t, value in entries:
                records.append({"metric": name, "t": t, "value": value})
        if not records:
            return DataFrame([])
        return DataFrame.from_records(records)

    def merge(self, other: "Metrics") -> None:
        for name, value in other.counters.items():
            self.inc(name, value)
        for name, entries in other.series.items():
            for t, value in entries:
                self.observe(name, value, t)

    def clear(self) -> None:
        self.counters.clear()
        self.series.clear()

    def summary(self, keys: Iterable[str]) -> dict[str, float]:
        result: dict[str, float] = {}
        for key in keys:
            if key in self.counters:
                result[key] = self.counters[key]
            elif key in self.series and self.series[key]:
                result[key] = self.series[key][-1][1]
        return result
