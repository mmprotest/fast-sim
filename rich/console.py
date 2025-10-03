"""Minimal Rich console stub."""
from __future__ import annotations


class Console:
    def print(self, *args, **kwargs) -> None:  # pragma: no cover - simple stub
        text = " ".join(str(arg) for arg in args)
        print(text)
