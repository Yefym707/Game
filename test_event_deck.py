import os
import random
import os
import sys

# Ensure the ``src`` directory is importable when tests are executed from the
# repository root.  This mirrors the approach used in the existing test suite.
sys.path.append(os.path.join(os.path.dirname(__file__), "src"))

from event_deck import GameState, load_events, EventDeck, draw_event
from game_board import GameBoard
from player import Player


def test_horde_event_spawns_zombies():
    events = load_events()
    board = GameBoard(5, 5)
    state = GameState(board, [])
    events["horde"].apply(state)
    assert len(state.zombies) == 3


def test_storm_damages_players():
    events = load_events()
    board = GameBoard(3, 3)
    p1 = Player(0, 0, health=5)
    state = GameState(board, [p1])
    events["storm"].apply(state)
    assert p1.health == 4


def test_draw_event_respects_weights():
    events = load_events()
    # Construct a small deterministic deck: only two events, one with weight 0
    subset = {eid: events[eid] for eid in ("horde", "storm")}
    weights = {"horde": 1, "storm": 0}
    deck = EventDeck(subset, weights)
    board = GameBoard(3, 3)
    state = GameState(board, [Player()])
    ev = draw_event(state, deck)
    assert ev.event_id == "horde"
