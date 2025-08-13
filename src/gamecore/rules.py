from __future__ import annotations

"""Rule helpers used by the simplified test implementation.

Only a sliver of the original rule set is required for the unit tests.  The
module defines a couple of constants (board size, action point costs and attack
ranges) and implements high level helpers that operate on the :class:`Board`
and :class:`GameState` objects from :mod:`gamecore.board`.
"""

from dataclasses import dataclass
from typing import Tuple

from . import events, validate

# general configuration -------------------------------------------------------
BOARD_SIZE = 5
MAX_AP = 3
MOVE_COST = 1
ATTACK_COST = 1
MOVE_RANGE = 3
ATTACK_RANGE = 1


# turn handling ---------------------------------------------------------------

def start_turn(state) -> None:
    player = state.current
    player.ap = MAX_AP  # type: ignore[attr-defined]


def end_turn(state) -> None:
    state.log.append(events.END_TURN)
    state.active = (state.active + 1) % len(state.players)
    state.turn += 1
    start_turn(state)


# actions --------------------------------------------------------------------

def move(state, dest: Tuple[int, int]) -> Tuple[bool, str | None]:
    reason = validate.can_move(state, dest)
    if reason:
        return False, reason
    player = state.current
    path = state.board.find_path((player.x, player.y), dest)
    steps = len(path) - 1
    player.x, player.y = dest
    player.ap -= steps  # type: ignore[operator]
    state.log.append(events.MOVE)
    return True, None


def attack(state, target) -> Tuple[bool, str | None]:
    reason = validate.can_attack(state, target)
    if reason:
        return False, reason
    player = state.current
    player.ap -= ATTACK_COST  # type: ignore[operator]
    target.health -= 3
    state.log.append(events.HIT)
    return True, None


__all__ = [
    "BOARD_SIZE",
    "MAX_AP",
    "MOVE_COST",
    "ATTACK_COST",
    "MOVE_RANGE",
    "ATTACK_RANGE",
    "start_turn",
    "end_turn",
    "move",
    "attack",
]
