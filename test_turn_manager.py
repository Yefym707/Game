"""Tests for the :mod:`turn_manager` module."""

import os
import sys

# Ensure the ``src`` directory is importable when tests are executed from the
# repository root, mirroring other tests in this suite.
sys.path.append(os.path.join(os.path.dirname(__file__), "src"))

from event_deck import GameState, Event, EventDeck
from game_board import GameBoard
from player import Player
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


def test_end_of_round_triggers_event(monkeypatch, capsys):
    board = GameBoard(3, 3)
    p1, p2 = Player(), Player()
    state = GameState(board=board, players=[p1, p2])

    def ambush(gs):
        for pl in gs.players:
            pl.take_damage(1)

    event = Event(event_id="ambush", description="Ambush!", effect=ambush)
    deck = EventDeck({"ambush": event}, {"ambush": 1})
    tm = turn_manager.TurnManager([p1, p2], game_state=state, event_deck=deck)

    monkeypatch.setattr(turn_manager.dice, "roll", lambda _: (1, ""))

    tm.start_turn()
    tm.end_turn()
    tm.start_turn()
    tm.end_turn()

    assert p1.health == 4
    assert p2.health == 4
    out = capsys.readouterr().out
    assert "Ambush!" in out

