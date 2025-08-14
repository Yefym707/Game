import os
import sys
import random


# Ensure the ``src`` directory is importable when tests are executed from the
# repository root.  This mirrors the approach used in the existing test suite.
sys.path.append(os.path.join(os.path.dirname(__file__), "src"))

from event_deck import (
    DEFAULT_DECK,
    Event,
    EventDeck,
    GameState,
    draw_event,
)
from game_board import GameBoard
from player import Player


def _get_event(description: str) -> Event:
    """Return the event with ``description`` from the default deck."""

    for ev in DEFAULT_DECK.events:
        if ev.description == description:
            return ev
    raise AssertionError(f"Event {description!r} not found in deck")


def test_zombie_horde_spawns_between_one_and_three_zombies():
    board = GameBoard(5, 5)
    state = GameState(board, [])
    event = _get_event("Zombie Horde")
    random.seed(0)
    event.apply(state)

    # Count zombies on the board
    zombies = [
        (x, y)
        for y, row in enumerate(board.grid)
        for x, cell in enumerate(row)
        if cell == "Z"
    ]
    assert 1 <= len(zombies) <= 3
    # The GameState keeps track of spawned zombies as well
    assert zombies == state.zombies


def test_ambush_damages_all_players():
    board = GameBoard(3, 3)
    p1 = Player(0, 0, health=5)
    p2 = Player(1, 1, health=4)
    state = GameState(board, [p1, p2])
    event = _get_event("Ambush")
    event.apply(state)
    assert p1.health == 4
    assert p2.health == 3


def test_draw_event_uses_provided_deck():
    board = GameBoard(3, 3)
    player = Player(0, 0, health=5)
    state = GameState(board, [player])
    # Create a deck containing only the ambush event to make the draw deterministic
    ambush = _get_event("Ambush")
    deck = EventDeck([ambush])
    drawn = draw_event(state, deck.events)
    assert drawn.description == "Ambush"
    assert player.health == 4

