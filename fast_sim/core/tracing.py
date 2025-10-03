"""Structured trace writer for simulations."""
from __future__ import annotations

import os
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any, IO

try:  # pragma: no cover - optional dependency
    import orjson
except Exception:  # pragma: no cover - fallback
    orjson = None
import json


def _serialize(record: dict[str, Any]) -> str:
    if orjson is not None:  # pragma: no branch
        return orjson.dumps(record).decode("utf-8")
    return json.dumps(record)


@dataclass
class Tracer:
    """Write JSONL trace entries when enabled."""

    path: Path
    enabled: bool = True
    _fh: IO[str] | None = None

    def __post_init__(self) -> None:
        if self.enabled:
            self._fh = self.path.open("w", encoding="utf-8")

    def record(self, kind: str, **payload: Any) -> None:
        if not self.enabled or self._fh is None:
            return
        record = {"ts": time.time(), "kind": kind, **payload}
        self._fh.write(_serialize(record) + "\n")
        self._fh.flush()

    def close(self) -> None:
        if self._fh is not None:
            self._fh.close()
            self._fh = None

    def __enter__(self) -> "Tracer":  # pragma: no cover - trivial
        return self

    def __exit__(self, *exc: Any) -> None:  # pragma: no cover - trivial
        self.close()


def build_tracer(path: Path | None = None, enabled: bool | None = None) -> Tracer:
    if enabled is None:
        enabled = bool(os.getenv("FAST_SIM_TRACE"))
    if path is None:
        path = Path("trace.jsonl")
    return Tracer(path=path, enabled=enabled)
