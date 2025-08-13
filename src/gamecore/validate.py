from __future__ import annotations

"""Validation helpers for the tiny test rule set.

Each function returns ``None`` when the action is permitted.  When the action is
not allowed a *localised* reason string is returned.  The strings are looked up
through :func:`gamecore.i18n.gettext` so the tests exercise the localisation
plumbing as well.
"""

from typing import Tuple

from .i18n import gettext as _
from . import rules


def _manhattan(a: Tuple[int, int], b: Tuple[int, int]) -> int:
    return abs(a[0] - b[0]) + abs(a[1] - b[1])


def can_move(state, dest: Tuple[int, int]) -> str | None:
    player = state.current
    path = state.board.find_path((player.x, player.y), dest)
    if not path:
        return _("blocked")
    steps = len(path) - 1
    if steps > rules.MOVE_RANGE:
        return _("out_of_range")
    if steps * rules.MOVE_COST > getattr(player, "ap", 0):
        return _("out_of_ap")
    return None


def can_attack(state, target) -> str | None:
    player = state.current
    dist = _manhattan((player.x, player.y), (target.x, target.y))
    if dist > rules.ATTACK_RANGE:
        return _("out_of_range")
    if getattr(player, "ap", 0) < rules.ATTACK_COST:
        return _("out_of_ap")
    return None


def can_end_turn(state) -> str | None:  # pragma: no cover - trivial
    return None


__all__ = ["can_move", "can_attack", "can_end_turn"]
