"""Deterministic random number helpers without NumPy."""
from __future__ import annotations

import hashlib
import math
import random
from dataclasses import dataclass, field
from typing import Any, Iterable, List, Sequence


def _hash_seed(seed: int | None, key: str) -> int:
    base = 0 if seed is None else seed
    payload = f"{base}:{key}".encode("utf-8")
    digest = hashlib.sha256(payload).digest()
    return int.from_bytes(digest[:8], "little")


@dataclass(slots=True)
class RNG:
    seed: int | None = None
    _random: random.Random = field(init=False, repr=False)

    def __post_init__(self) -> None:
        internal_seed = self.seed if self.seed is not None else random.randrange(2**32)
        self._random = random.Random(internal_seed)
        self.seed = internal_seed

    def spawn(self, key: str) -> "RNG":
        return RNG(_hash_seed(self.seed, key))

    # Convenience methods -------------------------------------------------
    def integers(self, low: int, high: int | None = None, size: int | tuple[int, ...] | None = None) -> int | List[int]:
        if high is None:
            high = low
            low = 0
        count = _to_size(size)
        if count == 1:
            return self._random.randrange(low, high)
        return [self._random.randrange(low, high) for _ in range(count)]

    def choice(
        self,
        a: Sequence[int] | int,
        size: int | tuple[int, ...] | None = None,
        replace: bool = True,
        p: Sequence[float] | None = None,
    ) -> Any:
        population = list(range(a)) if isinstance(a, int) else list(a)
        count = _to_size(size)
        if count == 1:
            return self._weighted_choice(population, p)
        if not replace and count > len(population):
            raise ValueError("Cannot take a larger sample than population when replace=False")
        if replace:
            return [self._weighted_choice(population, p) for _ in range(count)]
        sample = population.copy()
        self._random.shuffle(sample)
        return sample[:count]

    def normal(self, loc: float = 0.0, scale: float = 1.0, size: int | tuple[int, ...] | None = None) -> float | List[float]:
        count = _to_size(size)
        if count == 1:
            return self._random.gauss(loc, scale)
        return [self._random.gauss(loc, scale) for _ in range(count)]

    def poisson(self, lam: float = 1.0, size: int | tuple[int, ...] | None = None) -> int | List[int]:
        count = _to_size(size)
        def draw() -> int:
            l = math.exp(-lam)
            k = 0
            prod = 1.0
            while prod > l:
                k += 1
                prod *= self._random.random()
            return k - 1
        if count == 1:
            return draw()
        return [draw() for _ in range(count)]

    def exponential(self, scale: float = 1.0, size: int | tuple[int, ...] | None = None) -> float | List[float]:
        count = _to_size(size)
        rate = 1.0 / scale
        if count == 1:
            return self._random.expovariate(rate)
        return [self._random.expovariate(rate) for _ in range(count)]

    def uniform(self, low: float = 0.0, high: float = 1.0, size: int | tuple[int, ...] | None = None) -> float | List[float]:
        count = _to_size(size)
        if count == 1:
            return self._random.uniform(low, high)
        return [self._random.uniform(low, high) for _ in range(count)]

    def binomial(self, n: int, p: float, size: int | tuple[int, ...] | None = None) -> int | List[int]:
        count = _to_size(size)
        def draw() -> int:
            successes = 0
            for _ in range(n):
                if self._random.random() < p:
                    successes += 1
            return successes
        if count == 1:
            return draw()
        return [draw() for _ in range(count)]

    def shuffle(self, x: list[Any]) -> None:
        self._random.shuffle(x)

    def beta(self, a: float, b: float, size: int | tuple[int, ...] | None = None) -> float | List[float]:
        count = _to_size(size)
        if count == 1:
            return self._random.betavariate(a, b)
        return [self._random.betavariate(a, b) for _ in range(count)]

    def gamma(self, shape: float, scale: float = 1.0, size: int | tuple[int, ...] | None = None) -> float | List[float]:
        count = _to_size(size)
        if count == 1:
            return self._random.gammavariate(shape, scale)
        return [self._random.gammavariate(shape, scale) for _ in range(count)]

    def random(self, size: int | tuple[int, ...] | None = None) -> float | List[float]:
        count = _to_size(size)
        if count == 1:
            return self._random.random()
        return [self._random.random() for _ in range(count)]

    def _weighted_choice(self, population: Sequence[Any], weights: Sequence[float] | None) -> Any:
        if not population:
            raise ValueError("Cannot choose from an empty sequence")
        if weights is None:
            return population[self._random.randrange(0, len(population))]
        total = sum(weights)
        r = self._random.uniform(0, total)
        upto = 0.0
        for item, weight in zip(population, weights):
            upto += weight
            if upto >= r:
                return item
        return population[-1]


def _to_size(size: int | tuple[int, ...] | None) -> int:
    if size is None:
        return 1
    if isinstance(size, tuple):
        result = 1
        for dim in size:
            result *= dim
        return result
    return size
