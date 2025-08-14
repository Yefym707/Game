"""Tests for the :mod:`turn_manager` module."""

from typing import Any

import turn_manager


class Dummy:
    """Very small stand-in for a player or enemy."""

    def __init__(self, name: str) -> None:
        self.name = name


def test_start_turn_rolls_actions(monkeypatch):
    players = [Dummy("p1")]
    tm = turn_manager.TurnManager(players)

    # Ensure deterministic dice results.
    monkeypatch.setattr(turn_manager.dice, "roll", lambda _: (4, ""))

    player, actions = tm.start_turn()
    assert player is players[0]
    assert actions == 4
    assert tm.actions_left == 4


def test_round_progression(monkeypatch):
    players = [Dummy("p1"), Dummy("p2")]
    tm = turn_manager.TurnManager(players)

    monkeypatch.setattr(turn_manager.dice, "roll", lambda _: (1, ""))

    tm.start_turn()  # p1
    tm.end_turn()    # switch to p2
    tm.start_turn()  # p2
    tm.end_turn()    # new round, back to p1

    assert tm.round == 2
    assert tm.current_player is players[0]

