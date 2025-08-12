from __future__ import annotations

from typing import Iterable

from . import board as board_module


def _check_in_bounds(b: board_module.Board, x: int, y: int) -> bool:
    return 0 <= x < b.width and 0 <= y < b.height


def validate_state(state: board_module.GameState) -> None:
    """Validate basic invariants of ``state``.

    Raises ``ValueError`` when an inconsistency is detected.
    """

    b = state.board
    if len(b.tiles) != b.height:
        raise ValueError("invalid board height")
    for row in b.tiles:
        if len(row) != b.width:
            raise ValueError("invalid board width")
    for (x, y) in b.noise.keys():
        if not _check_in_bounds(b, x, y):
            raise ValueError("noise out of bounds")
    player_pos = set()
    for p in state.players:
        if not _check_in_bounds(b, p.x, p.y):
            raise ValueError("entity out of bounds")
        pos = (p.x, p.y)
        if pos in player_pos:
            raise ValueError("player collision")
        player_pos.add(pos)
    zombie_pos = set()
    for z in state.zombies:
        if not _check_in_bounds(b, z.x, z.y):
            raise ValueError("entity out of bounds")
        pos = (z.x, z.y)
        if pos in zombie_pos:
            raise ValueError("zombie collision")
        zombie_pos.add(pos)
    for p in state.players:
        if not all(isinstance(it, str) for it in p.inventory):
            raise ValueError("invalid inventory item")
    if not 0 <= state.active < len(state.players):
        raise ValueError("invalid active index")
