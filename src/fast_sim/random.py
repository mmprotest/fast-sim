"""Deterministic random number generation utilities."""
from __future__ import annotations

from typing import Optional

import numpy as np

__all__ = ["set_seed", "get_rng"]


_rng: Optional[np.random.Generator] = None


def set_seed(seed: int) -> None:
    """Initialise the module-level random generator.

    Parameters
    ----------
    seed:
        Seed to initialise the global RNG. Re-initialises the generator when called.
    """

    global _rng
    _rng = np.random.default_rng(int(seed))


def get_rng() -> np.random.Generator:
    """Return the module-level random number generator.

    Returns
    -------
    numpy.random.Generator
        The deterministic RNG instance. If not yet initialised, it defaults to seed 0.
    """

    global _rng
    if _rng is None:
        _rng = np.random.default_rng(0)
    return _rng
