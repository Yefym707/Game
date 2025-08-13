from __future__ import annotations

"""Tiny board and game state helpers used by the tests.

The original project ships with a large and feature rich implementation.  For
unit tests we only require a light‑weight subset that can create a board,
perform very small path finding and keep track of a couple of players.  The
functions implemented here intentionally mirror the API of the real project so
other modules (``rules`` and ``validate``) can interact with it without pulling
in heavy dependencies.
"""

from dataclasses import dataclass, field
from typing import Dict, Iterable, List, Tuple

from . import entities, rules


# ---------------------------------------------------------------------------
# Basic board structure
# ---------------------------------------------------------------------------


@dataclass
class Board:
    width: int
    height: int
    tiles: List[List[str]]  # ``.`` = floor, ``#`` = wall

    @classmethod
    def generate(cls, width: int, height: int) -> "Board":
        tiles = [["." for _ in range(width)] for _ in range(height)]
        return cls(width, height, tiles)

    # simple helpers -----------------------------------------------------
    def in_bounds(self, x: int, y: int) -> bool:
        return 0 <= x < self.width and 0 <= y < self.height

    def is_walkable(self, x: int, y: int) -> bool:
        return self.in_bounds(x, y) and self.tiles[y][x] != "#"

    # path finding -------------------------------------------------------
    def find_path(self, start: Tuple[int, int], goal: Tuple[int, int]) -> List[Tuple[int, int]]:
        """Return a list of cells from ``start`` to ``goal``.

        The algorithm is a simple breadth first search operating on the four
        cardinal neighbours.  Walls (``#``) are treated as solid and the result
        includes both ``start`` and ``goal`` when a route exists.  An empty list
        indicates that ``goal`` is unreachable.
        """

        if start == goal:
            return [start]

        sx, sy = start
        gx, gy = goal
        frontier = [(sx, sy)]
        came_from: Dict[Tuple[int, int], Tuple[int, int] | None] = {start: None}
        for cx, cy in frontier:
            for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                nx, ny = cx + dx, cy + dy
                if not self.is_walkable(nx, ny) or (nx, ny) in came_from:
                    continue
                frontier.append((nx, ny))
                came_from[(nx, ny)] = (cx, cy)
                if (nx, ny) == goal:
                    frontier = []
                    break

        if goal not in came_from:
            return []
        # reconstruct path
        path = [goal]
        cur = goal
        while came_from[cur] is not None:
            cur = came_from[cur]  # type: ignore[assignment]
            path.append(cur)
        path.reverse()
        return path


# ---------------------------------------------------------------------------
# Game state
# ---------------------------------------------------------------------------


@dataclass
class GameState:
    board: Board
    players: List[entities.Player]
    active: int = 0
    turn: int = 0
    log: List[str] = field(default_factory=list)

    @property
    def current(self) -> entities.Player:
        return self.players[self.active]


def create_game(width: int = rules.BOARD_SIZE, height: int = rules.BOARD_SIZE, players: int = 1) -> GameState:
    """Create a small dummy game used in tests."""

    board = Board.generate(width, height)
    plist: List[entities.Player] = []
    for i in range(players):
        p = entities.Player(i, 0, "@", id=i, team=i)
        p.ap = rules.MAX_AP  # type: ignore[attr-defined]
        plist.append(p)
    return GameState(board, plist)


__all__ = ["Board", "GameState", "create_game"]
