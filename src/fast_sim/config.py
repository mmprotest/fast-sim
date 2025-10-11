"""Configuration handling for fast_sim."""
from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, MutableMapping, Optional

from pydantic import BaseModel, Field, validator

from .random import set_seed

try:  # optional dependency
    import yaml
except ModuleNotFoundError:  # pragma: no cover
    yaml = None  # type: ignore


class SimConfig(BaseModel):
    """Simulation configuration model."""

    seed: int = 42
    n_agents: int = Field(..., gt=0, description="Number of agents in the simulation.")
    steps: int = Field(..., gt=0, description="Number of steps to run by default.")
    params: Dict[str, Any] = Field(default_factory=dict)
    record_every: int = Field(1, gt=0, description="Record metrics every N steps.")

    @validator("seed")
    def _coerce_seed(cls, value: int) -> int:
        return int(value)

    @validator("params", pre=True)
    def _ensure_params(cls, value: Optional[MutableMapping[str, Any]]) -> Dict[str, Any]:
        if value is None:
            return {}
        return dict(value)

    def apply_seed(self) -> None:
        """Apply the configuration seed to the global RNG."""

        set_seed(self.seed)


def load_config(path: str | Path) -> SimConfig:
    """Load a :class:`SimConfig` from a YAML file."""

    if yaml is None:
        raise ImportError("pyyaml is required to load YAML configuration files.")
    data = yaml.safe_load(Path(path).read_text())
    if not isinstance(data, dict):
        raise ValueError("Configuration file must define a mapping at the top level.")
    return SimConfig(**data)


__all__ = ["SimConfig", "load_config"]
