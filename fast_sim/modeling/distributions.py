"""Sampling helpers with stable APIs."""
from __future__ import annotations

import math
from typing import Any, Callable, Sequence

from pandas import DataFrame

from ..core.rng import RNG


def uniform(rng: RNG, low: float, high: float, size: int | tuple[int, ...] = 1) -> np.ndarray:
    return rng.uniform(low=low, high=high, size=size)


def normal(rng: RNG, mean: float, std: float, size: int | tuple[int, ...] = 1) -> np.ndarray:
    return rng.normal(loc=mean, scale=std, size=size)


def exponential(rng: RNG, rate: float, size: int | tuple[int, ...] = 1) -> np.ndarray:
    scale = 1.0 / rate
    return rng.exponential(scale=scale, size=size)


def lognormal(rng: RNG, mean: float, sigma: float, size: int | tuple[int, ...] = 1) -> list[float] | float:
    count = size if isinstance(size, int) else size[0]
    def draw() -> float:
        normal = rng.normal(loc=mean, scale=sigma)
        if isinstance(normal, list):
            return [math.exp(x) for x in normal]
        return math.exp(normal)
    if isinstance(size, tuple) or count != 1:
        values = rng.normal(loc=mean, scale=sigma, size=size)
        if isinstance(values, list):
            return [math.exp(x) for x in values]
        return [math.exp(values)]
    value = rng.normal(loc=mean, scale=sigma)
    if isinstance(value, list):
        return [math.exp(x) for x in value]
    return math.exp(value)


def poisson(rng: RNG, lam: float, size: int | tuple[int, ...] = 1) -> list[int] | int:
    return rng.poisson(lam=lam, size=size)


def mixture(rng: RNG, components: Sequence[tuple[float, Callable[[RNG, int], Sequence[float]]]], size: int) -> list[float]:
    total = sum(weight for weight, _ in components)
    weights = [weight / total for weight, _ in components]
    choices_raw = rng.choice(len(components), size=size, p=weights)
    choices = choices_raw if isinstance(choices_raw, list) else [choices_raw]
    out = [0.0 for _ in range(size)]
    for idx, (_, sampler) in enumerate(components):
        indices = [i for i, value in enumerate(choices) if value == idx]
        if indices:
            draws = sampler(rng, len(indices))
            for dest, value in zip(indices, draws):
                out[dest] = value
    return out


def empirical_from_data(df: DataFrame, column: str) -> Callable[[RNG, int], list[Any]]:
    values = [value for value in df[column] if value is not None]
    if len(values) == 0:
        raise ValueError("No data to sample from")

    def sampler(rng: RNG, size: int) -> list[Any]:
        return rng.choice(values, size=size, replace=True)

    return sampler
