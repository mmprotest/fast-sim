"""Configuration parsing without external dependencies."""
from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Callable, Dict, Iterable, List, Literal

from ..core.timeline import Schedule
from ..modeling.policies import Policy

from ruamel.yaml import YAML

try:  # pragma: no cover - optional TOML
    import tomllib
except Exception:  # pragma: no cover
    tomllib = None


@dataclass
class FieldConfig:
    dtype: str
    init: Any = 0

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "FieldConfig":
        return cls(dtype=str(data.get("dtype", "float")), init=data.get("init", 0))

    def to_dict(self) -> Dict[str, Any]:
        return {"dtype": self.dtype, "init": self.init}


@dataclass
class StateConfig:
    size: int
    fields: Dict[str, FieldConfig]

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "StateConfig":
        fields = {name: FieldConfig.from_dict(value) for name, value in data.get("fields", {}).items()}
        return cls(size=int(data["size"]), fields=fields)

    def to_dict(self) -> Dict[str, Any]:
        return {"size": self.size, "fields": {name: cfg.to_dict() for name, cfg in self.fields.items()}}


@dataclass
class PolicyScheduleConfig:
    at: List[float] | None = None
    every: float | None = None
    start: float = 0.0

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "PolicyScheduleConfig":
        return cls(
            at=list(data.get("at")) if data.get("at") is not None else None,
            every=data.get("every"),
            start=float(data.get("start", 0.0)),
        )

    def build(self) -> Schedule:
        if self.at:
            return Schedule(at=self.at)
        if self.every is not None:
            return Schedule(every=self.every, start=self.start)
        raise ValueError("Schedule requires 'at' or 'every'")


@dataclass
class PolicyConfig:
    name: str
    when: Literal["time-step", "event"]
    callable: str
    schedule: PolicyScheduleConfig | None = None

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "PolicyConfig":
        schedule = data.get("schedule")
        return cls(
            name=data["name"],
            when=data["when"],
            callable=data["callable"],
            schedule=PolicyScheduleConfig.from_dict(schedule) if schedule else None,
        )

    def build(self) -> Policy:
        func = import_callable(self.callable)
        schedule = self.schedule.build() if self.schedule else None
        return Policy(name=self.name, when=self.when, func=func, schedule=schedule)

    def to_dict(self) -> Dict[str, Any]:
        payload = {"name": self.name, "when": self.when, "callable": self.callable}
        if self.schedule:
            payload["schedule"] = {
                "at": self.schedule.at,
                "every": self.schedule.every,
                "start": self.schedule.start,
            }
        return payload


@dataclass
class StepEngineConfig:
    type: Literal["step"] = "step"
    dt: float = 1.0
    horizon: float = 1.0
    tick: str = ""

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "StepEngineConfig":
        return cls(dt=float(data["dt"]), horizon=float(data["horizon"]), tick=data["tick"])

    def to_dict(self) -> Dict[str, Any]:
        return {"type": self.type, "dt": self.dt, "horizon": self.horizon, "tick": self.tick}


@dataclass
class EventEngineConfig:
    type: Literal["event"] = "event"
    until: float | None = None
    handler: str = ""
    initial_events: List[Dict[str, Any]] = field(default_factory=list)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "EventEngineConfig":
        return cls(
            until=data.get("until"),
            handler=data["handler"],
            initial_events=[dict(event) for event in data.get("initial_events", [])],
        )

    def to_dict(self) -> Dict[str, Any]:
        return {
            "type": self.type,
            "until": self.until,
            "handler": self.handler,
            "initial_events": [dict(evt) for evt in self.initial_events],
        }


@dataclass
class OutputConfig:
    path: str = "runs"
    format: Literal["parquet", "csv"] = "parquet"

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "OutputConfig":
        return cls(path=data.get("path", "runs"), format=data.get("format", "parquet"))

    def to_dict(self) -> Dict[str, Any]:
        return {"path": self.path, "format": self.format}


@dataclass
class Config:
    state: StateConfig
    engine: StepEngineConfig | EventEngineConfig
    seed: int | None = None
    policies: List[PolicyConfig] = field(default_factory=list)
    output: OutputConfig = field(default_factory=OutputConfig)
    sweep: Dict[str, List[Any]] | None = None

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Config":
        state = StateConfig.from_dict(data["state"])
        engine_data = data["engine"]
        engine_type = engine_data.get("type", "step")
        if engine_type == "step":
            engine = StepEngineConfig.from_dict(engine_data)
        else:
            engine = EventEngineConfig.from_dict(engine_data)
        policies = [PolicyConfig.from_dict(p) for p in data.get("policies", [])]
        output = OutputConfig.from_dict(data.get("output", {}))
        sweep = data.get("sweep")
        return cls(
            state=state,
            engine=engine,
            seed=data.get("seed"),
            policies=policies,
            output=output,
            sweep=sweep,
        )

    @classmethod
    def model_validate(cls, data: Dict[str, Any]) -> "Config":  # compatibility alias
        return cls.from_dict(data)

    def to_dict(self) -> Dict[str, Any]:
        payload = {
            "state": self.state.to_dict(),
            "engine": self.engine.to_dict(),
            "seed": self.seed,
            "policies": [policy.to_dict() for policy in self.policies],
            "output": self.output.to_dict(),
            "sweep": self.sweep,
        }
        return payload

    def model_dump(self, mode: str = "python") -> Dict[str, Any]:  # compatibility
        return self.to_dict()


def import_callable(path: str) -> Callable[..., Any]:
    module, _, attr = path.partition(":")
    if not attr:
        module, _, attr = path.rpartition(".")
    if not module or not attr:
        raise ValueError(f"Invalid callable path: {path}")
    mod = __import__(module, fromlist=[attr])
    func = getattr(mod, attr)
    if not callable(func):
        raise TypeError(f"{path} is not callable")
    return func


def load_config(path: str | Path) -> Config:
    path = Path(path)
    text = path.read_text()
    if path.suffix in {".yaml", ".yml", ""}:
        yaml = YAML(typ="safe")
        data = yaml.load(text)
    elif path.suffix == ".toml":
        if tomllib is None:
            raise RuntimeError("TOML support requires Python 3.11+")
        data = tomllib.loads(text)
    else:
        raise ValueError(f"Unsupported config extension: {path.suffix}")
    return Config.from_dict(data)
