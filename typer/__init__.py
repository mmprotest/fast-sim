"""Minimal subset of Typer for fast-sim."""
from __future__ import annotations

import inspect
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable, Dict, Iterable, List


class BadParameter(Exception):
    pass


@dataclass
class Option:
    default: Any = ...
    help: str | None = None


class Command:
    def __init__(self, func: Callable[..., Any]) -> None:
        self.func = func
        self.signature = inspect.signature(func)


class Typer:
    def __init__(self, help: str | None = None) -> None:
        self.help = help
        self._commands: Dict[str, Command] = {}

    def command(self, name: str | None = None) -> Callable[[Callable[..., Any]], Callable[..., Any]]:
        def decorator(func: Callable[..., Any]) -> Callable[..., Any]:
            cmd_name = name or func.__name__
            self._commands[cmd_name] = Command(func)
            return func

        return decorator

    def _invoke(self, argv: Iterable[str], standalone: bool = False) -> int:
        args = list(argv)
        if not args:
            if standalone:
                print(self.help or "")
            return 0
        cmd_name = args.pop(0)
        if cmd_name not in self._commands:
            raise BadParameter(f"Unknown command {cmd_name}")
        command = self._commands[cmd_name]
        try:
            parsed = _parse_arguments(command, args)
            command.func(**parsed)
            return 0
        except Exception as exc:  # pragma: no cover - defensive
            if standalone:
                print(f"Error: {exc}")
            return 1

    def __call__(self) -> None:  # pragma: no cover - manual use
        exit_code = self._invoke(sys.argv[1:], standalone=True)
        sys.exit(exit_code)


def _parse_arguments(command: Command, args: List[str]) -> Dict[str, Any]:
    remaining = list(args)
    parsed: Dict[str, Any] = {}
    for param in command.signature.parameters.values():
        default = param.default
        annotation = param.annotation
        if isinstance(default, Option):
            flag = f"--{param.name.replace('_', '-')}"
            value = default.default
            if flag in remaining:
                idx = remaining.index(flag)
                if idx + 1 >= len(remaining):
                    raise BadParameter(f"Missing value for {flag}")
                value = remaining[idx + 1]
                del remaining[idx : idx + 2]
            if value is ...:
                raise BadParameter(f"Missing option {flag}")
            parsed[param.name] = _convert(value, annotation)
        else:
            if not remaining:
                raise BadParameter(f"Missing argument {param.name}")
            value = remaining.pop(0)
            parsed[param.name] = _convert(value, annotation)
    return parsed


def _convert(value: Any, annotation: Any) -> Any:
    if isinstance(annotation, str):
        if annotation == "Path":
            return Path(value)
        if annotation == "int":
            return int(value)
        if annotation == "float":
            return float(value)
        if annotation == "bool":
            return str(value).lower() not in {"0", "false", "no"}
        return value
    if annotation is Path:
        return Path(value)
    if annotation in {int, float}:
        return annotation(value)
    if annotation is bool:
        return value.lower() not in {"0", "false", "no"}
    return value


class Result:
    def __init__(self, exit_code: int, stdout: str = "") -> None:
        self.exit_code = exit_code
        self.stdout = stdout


class CliRunner:
    def invoke(self, app: Typer, args: List[str]) -> Result:
        exit_code = app._invoke(args, standalone=False)
        return Result(exit_code)


__all__ = ["Typer", "Option", "BadParameter", "CliRunner"]
