"""Tiny YAML helper for fast-sim."""
from __future__ import annotations

import json
from typing import Any


class YAML:
    def __init__(self, typ: str | None = None) -> None:
        self.typ = typ

    def load(self, text: str) -> Any:
        text = text.strip()
        if not text:
            return {}
        try:
            return json.loads(text)
        except json.JSONDecodeError as exc:  # pragma: no cover - defensive
            raise ValueError("Minimal YAML loader only supports JSON syntax") from exc

    def dump(self, data: Any, stream) -> None:
        text = json.dumps(data, indent=2)
        stream.write(text)
