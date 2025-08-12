from __future__ import annotations

from collections import deque
from typing import Dict, Iterable, List, Set, Tuple

from . import rules
from . import board as board_mod
from . import entities


def _find_path(board: board_mod.Board, state: board_mod.GameState, start: Tuple[int, int], goals: Set[Tuple[int, int]], zombie: entities.Zombie) -> List[Tuple[int, int]]:
    if not goals:
        return []
    queue = deque([(start, [])])
    visited = {start}
    blocked = {(z.x, z.y) for z in state.zombies if z is not zombie}
    while queue:
        (x, y), path = queue.popleft()
        if (x, y) in goals and path:
            return path
        for dx, dy in rules.DIRECTIONS.values():
            nx, ny = x + dx, y + dy
            if not board.in_bounds(nx, ny):
                continue
            if not board.is_empty(nx, ny) and (nx, ny) not in goals:
                continue
            if (nx, ny) in blocked and (nx, ny) not in goals:
                continue
            if (nx, ny) not in visited:
                visited.add((nx, ny))
                queue.append(((nx, ny), path + [(nx, ny)]))
    return []


def zombie_turns(state: board_mod.GameState) -> None:
    player_positions = {(p.x, p.y) for p in state.players}
    for z in state.zombies:
        targets = set(state.board.noise.keys())
        path = _find_path(state.board, state, (z.x, z.y), targets, z)
        if not path:
            path = _find_path(state.board, state, (z.x, z.y), player_positions, z)
        if path:
            nx, ny = path[0]
            z.x, z.y = nx, ny
        for p in state.players:
            if z.x == p.x and z.y == p.y:
                p.health -= 1
                state.add_log("zombie attack")
