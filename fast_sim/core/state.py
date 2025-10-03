"""Columnar agent state container using Python lists."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Callable, Iterable, Mapping

from pandas import DataFrame

Initializer = Callable[[int], list[Any]] | float | int | list[Any]


@dataclass(slots=True)
class StateView:
    state: "State"
    mask: list[bool]

    def arrays(self) -> Mapping[str, list[Any]]:
        return {name: [value for value, flag in zip(values, self.mask) if flag] for name, values in self.state._fields.items()}

    def as_dataframe(self) -> DataFrame:
        return DataFrame(self.arrays())

    def update(self, **kwargs: Any) -> None:
        self.state.update(self.mask, **kwargs)


class State:
    def __init__(self, size: int) -> None:
        self._size = size
        self._fields: dict[str, list[Any]] = {}

    @property
    def size(self) -> int:
        return self._size

    def add_field(self, name: str, dtype: Any, init: Initializer | None = None) -> None:
        if name in self._fields:
            raise ValueError(f"Field '{name}' already present")
        if init is None:
            default = 0.0 if isinstance(dtype, str) and "float" in dtype else 0
            values = [dtype() if callable(dtype) else default for _ in range(self._size)]
        elif callable(init):
            values = list(init(self._size))
        elif isinstance(init, list):
            values = list(init)
        else:
            values = [init for _ in range(self._size)]
        if len(values) != self._size:
            raise ValueError("Initialiser must produce list with length equal to state size")
        self._fields[name] = values

    def add_fields(self, **field_defs: tuple[Any, Initializer | None]) -> None:
        for name, (dtype, init) in field_defs.items():
            self.add_field(name, dtype, init)

    def __contains__(self, name: str) -> bool:
        return name in self._fields

    def __getitem__(self, name: str) -> list[Any]:
        return self._fields[name]

    def update(self, mask: list[bool] | Iterable[int], /, **updates: Any) -> None:
        if isinstance(mask, list):
            if len(mask) != self._size:
                raise ValueError("Mask must match state size")
            indices = [idx for idx, flag in enumerate(mask) if flag]
        else:
            indices = list(mask)
        for name, values in updates.items():
            if name not in self._fields:
                raise KeyError(name)
            field = self._fields[name]
            if isinstance(values, list):
                if len(values) != len(indices):
                    raise ValueError("Value list must match mask length")
                for idx, value in zip(indices, values):
                    field[idx] = value
            else:
                for idx in indices:
                    field[idx] = values

    def view(self, mask: list[bool] | Iterable[int]) -> StateView:
        if isinstance(mask, list):
            if len(mask) != self._size:
                raise ValueError("Mask must match state size")
            bool_mask = mask
        else:
            bool_mask = [False] * self._size
            for idx in mask:
                bool_mask[idx] = True
        return StateView(self, bool_mask)

    def as_dataframe(self, sample: int | None = None) -> DataFrame:
        data = {name: list(values) for name, values in self._fields.items()}
        df = DataFrame(data)
        if sample is not None and sample < len(df):
            df = df.sample(sample, random_state=0)
        return df.reset_index(drop=True)

    def resize(self, new_size: int) -> None:
        for name, values in self._fields.items():
            if new_size > self._size:
                values.extend([values[-1] if values else None for _ in range(new_size - self._size)])
            else:
                del values[new_size:]
        self._size = new_size

    def to_dict(self) -> Mapping[str, list[Any]]:
        return {k: list(v) for k, v in self._fields.items()}

    def __repr__(self) -> str:  # pragma: no cover
        return f"State(size={self._size}, fields={list(self._fields)})"
