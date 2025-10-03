"""Quick plotting helpers with lazy matplotlib imports."""
from __future__ import annotations

from typing import Iterable

import pandas as pd


def _require_matplotlib():  # pragma: no cover - visual utility
    try:
        import matplotlib.pyplot as plt
    except Exception as exc:  # pragma: no cover
        raise RuntimeError("matplotlib is required for plotting") from exc
    return plt


def plot_series(metrics: pd.DataFrame, keys: Iterable[str], ax=None) -> None:  # pragma: no cover
    plt = _require_matplotlib()
    ax = ax or plt.gca()
    for key in keys:
        subset = metrics[metrics["metric"] == key]
        ax.plot(subset["t"], subset["value"], label=key)
    ax.legend()
    ax.set_xlabel("t")
    ax.set_ylabel("value")


def hist(values, bins: int = 30, ax=None) -> None:  # pragma: no cover
    plt = _require_matplotlib()
    ax = ax or plt.gca()
    ax.hist(values, bins=bins)


def heatmap(grid: pd.DataFrame | "np.ndarray", ax=None) -> None:  # pragma: no cover
    plt = _require_matplotlib()
    ax = ax or plt.gca()
    if hasattr(grid, "values"):
        data = grid.values
    else:
        data = grid
    ax.imshow(data, cmap="viridis", origin="lower")
