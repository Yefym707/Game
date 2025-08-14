"""Simple random event system for the board game.

The original project this repository stems from featured a rather involved
event system driven by JSON data.  For the purposes of the unit tests in this
kata we provide a much smaller yet fully functional implementation.  Each
event carries a short description and a callable effect which manipulates the
current game state.  A small deck of sample events is included to demonstrate
how events may influence the board and players.

Events are deliberately lightweight and self‑contained which makes them easy to
extend in the future – simply create a new :class:`Event` instance and add it to
the deck.
"""

from __future__ import annotations

import random
from dataclasses import dataclass, field
from typing import Callable, Dict, List, Optional, Sequence, Tuple

from game_board import GameBoard
from player import Player


# ---------------------------------------------------------------------------
# Data structures
# ---------------------------------------------------------------------------


@dataclass
class GameState:
    """Minimal representation of the game's mutable state.

    The production project exposes a very feature rich state object.  For the
    tests we only require a board, a list of players, optional item locations
    and coordinates of existing zombies.  The structure is intentionally kept
    simple so it can easily be instantiated by the tests.
    """

    board: GameBoard
    players: List[Player]
    items: Dict[Tuple[int, int], str] = field(default_factory=dict)
    zombies: List[Tuple[int, int]] = field(default_factory=list)


@dataclass
class Event:
    """Representation of a single random event.

    Parameters
    ----------
    description:
        Human readable explanation of the event.
    effect:
        Callable which mutates the provided :class:`GameState`.
    """

    description: str
    effect: Callable[[GameState], None]

    def apply(self, game_state: GameState) -> None:
        """Execute the event's effect on ``game_state``."""

        self.effect(game_state)


@dataclass
class EventDeck:
    """Container holding a set of events.

    The :meth:`draw` method selects a random event, applies it and returns the
    chosen instance.  Using a dedicated class keeps the implementation flexible
    and mirrors a draw pile of physical cards.
    """

    events: List[Event]

    def draw(self, game_state: GameState) -> Event:
        """Pick a random event from the deck and apply it.

        Parameters
        ----------
        game_state:
            The current state to which the event's effect will be applied.

        Returns
        -------
        Event
            The event that was drawn and executed.
        """

        event = random.choice(self.events)
        event.apply(game_state)
        return event


# ---------------------------------------------------------------------------
# Event effect helpers
# ---------------------------------------------------------------------------


def _zombie_horde_effect(game_state: GameState) -> None:
    """Spawn one to three zombies at random free tiles."""

    count = random.randint(1, 3)
    placed = 0
    attempts = 0
    while placed < count and attempts < 100:
        x = random.randrange(game_state.board.width)
        y = random.randrange(game_state.board.height)
        if game_state.board.is_tile_free(x, y):
            game_state.board.place_entity(x, y, "Z")
            game_state.zombies.append((x, y))
            placed += 1
        attempts += 1


def _supply_drop_effect(game_state: GameState) -> None:
    """Place a random item on a random free tile."""

    item = random.choice(["food", "ammo", "medkit"])
    attempts = 0
    while attempts < 100:
        x = random.randrange(game_state.board.width)
        y = random.randrange(game_state.board.height)
        if game_state.board.is_tile_free(x, y) and (x, y) not in game_state.items:
            game_state.items[(x, y)] = item
            break
        attempts += 1


def _ambush_effect(game_state: GameState) -> None:
    """All players take one point of damage."""

    for player in game_state.players:
        player.take_damage(1)


# ---------------------------------------------------------------------------
# Default deck and drawing helper
# ---------------------------------------------------------------------------


DEFAULT_DECK = EventDeck(
    [
        Event("Zombie Horde", _zombie_horde_effect),
        Event("Supply Drop", _supply_drop_effect),
        Event("Ambush", _ambush_effect),
    ]
)


def draw_event(
    game_state: GameState, deck: Optional[Sequence[Event]] = None
) -> Event:
    """Select a random :class:`Event` from ``deck`` and apply it.

    Parameters
    ----------
    game_state:
        The mutable game state to be altered by the event.
    deck:
        Optional sequence of events to draw from.  When omitted the
        :data:`DEFAULT_DECK` is used.
    """

    if deck is None:
        deck = DEFAULT_DECK.events
    event = random.choice(list(deck))
    event.apply(game_state)
    return event


__all__ = [
    "GameState",
    "Event",
    "EventDeck",
    "DEFAULT_DECK",
    "draw_event",
]

