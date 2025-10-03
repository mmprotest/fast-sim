"""Spatial helpers for agent models."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable, Iterator, List, Tuple

try:  # pragma: no cover - optional
    import networkx as nx
except Exception:  # pragma: no cover
    nx = None


@dataclass
class Grid:
    width: int
    height: int

    def __post_init__(self) -> None:
        self._grid = [[-1 for _ in range(self.width)] for _ in range(self.height)]

    def coords(self) -> Iterator[tuple[int, int]]:
        for y in range(self.height):
            for x in range(self.width):
                yield x, y

    def neighbors(self, x: int, y: int) -> list[tuple[int, int]]:
        neigh: list[tuple[int, int]] = []
        for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            nx_, ny_ = x + dx, y + dy
            if 0 <= nx_ < self.width and 0 <= ny_ < self.height:
                neigh.append((nx_, ny_))
        return neigh

    def occupy(self, x: int, y: int, agent_id: int) -> None:
        self._grid[y][x] = agent_id

    def vacate(self, x: int, y: int) -> None:
        self._grid[y][x] = -1

    def is_empty(self, x: int, y: int) -> bool:
        return self._grid[y][x] < 0

    def density(self) -> float:
        occupied = sum(1 for row in self._grid for value in row if value >= 0)
        return float(occupied) / (self.width * self.height)

    def as_array(self) -> list[list[int]]:
        return [list(row) for row in self._grid]


class GraphSpace:
    """Thin wrapper for graph-based environments."""

    def __init__(self, edges: Iterable[tuple[int, int]]) -> None:
        if nx is not None:
            self._graph = nx.Graph()
            self._graph.add_edges_from(edges)
        else:
            self._graph = {}
            for u, v in edges:
                self._graph.setdefault(u, set()).add(v)
                self._graph.setdefault(v, set()).add(u)

    def neighbors(self, node: int) -> List[int]:
        if nx is not None:
            return list(self._graph.neighbors(node))
        return list(self._graph.get(node, []))

    def degree(self, node: int) -> int:
        return len(self.neighbors(node))
