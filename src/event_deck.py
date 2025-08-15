"""Random event handling based on JSON data files."""

from __future__ import annotations

import json
import os
import random
from dataclasses import dataclass, field
from typing import Callable, Dict, List, Optional, Tuple

from game_board import GameBoard
from player import Player


# ---------------------------------------------------------------------------
# Data structures
# ---------------------------------------------------------------------------


@dataclass
class GameState:
    """Minimal representation of the game's mutable state."""

    board: GameBoard
    players: List[Player]
    items: Dict[Tuple[int, int], str] = field(default_factory=dict)
    zombies: List[Tuple[int, int]] = field(default_factory=list)


@dataclass
class Event:
    """Representation of a single random event."""

    event_id: str
    description: str
    effect: Callable[[GameState], None]

    def apply(self, game_state: GameState) -> None:
        self.effect(game_state)


@dataclass
class EventDeck:
    """Container holding a set of events and their draw weights."""

    events: Dict[str, Event]
    weights: Dict[str, int]

    def draw(self, game_state: GameState) -> Event:
        ids = list(self.events.keys())
        weights = [self.weights.get(eid, 1) for eid in ids]
        chosen = random.choices(ids, weights=weights, k=1)[0]
        event = self.events[chosen]
        event.apply(game_state)
        return event


# ---------------------------------------------------------------------------
# Loading helpers
# ---------------------------------------------------------------------------

_DATA_DIR = os.path.join(os.path.dirname(__file__), '..', 'data')


def _apply_effect(game_state: GameState, effect: Dict[str, object]) -> None:
    """Apply a single effect description to ``game_state``."""

    hp = effect.get('hp')
    if hp:
        for pl in game_state.players:
            if hp > 0:
                pl.heal(int(hp))
            else:
                pl.take_damage(int(-hp))

    item = effect.get('add_item')
    if item:
        for pl in game_state.players:
            pl.pick_up(str(item))

    remove = effect.get('remove_item')
    if remove:
        for pl in game_state.players:
            try:
                pl.inventory.remove_item(str(remove))
            except Exception as exc:  # pragma: no cover - inventory may vary
                import logging

                logging.getLogger(__name__).debug(
                    "Failed removing %s from inventory: %s", remove, exc
                )

    spawn = effect.get('spawn_zombies')
    if spawn:
        count = int(spawn)
        placed = 0
        attempts = 0
        while placed < count and attempts < 100:
            x = random.randrange(game_state.board.width)
            y = random.randrange(game_state.board.height)
            if game_state.board.is_tile_free(x, y):
                game_state.board.place_entity(x, y, 'Z')
                game_state.zombies.append((x, y))
                placed += 1
            attempts += 1


def load_events(path: Optional[str] = None) -> Dict[str, Event]:
    """Load event definitions from JSON and return mapping of id -> Event."""

    path = path or os.path.join(_DATA_DIR, 'events.json')
    with open(path, 'r', encoding='utf-8') as fh:
        raw = json.load(fh)

    events: Dict[str, Event] = {}
    for entry in raw:
        effects = entry.get('effects', [])
        effect_data = effects[0] if effects else {}
        events[entry['id']] = Event(
            event_id=entry['id'],
            description=entry.get('id', ''),
            effect=lambda gs, ed=effect_data: _apply_effect(gs, ed),
        )
    return events


def load_deck_config(path: Optional[str] = None) -> Dict[str, int]:
    """Return the event draw weights from ``decks.json``."""

    path = path or os.path.join(_DATA_DIR, 'decks.json')
    with open(path, 'r', encoding='utf-8') as fh:
        data = json.load(fh)
    return data.get('events', {})


# Build default deck on import ------------------------------------------------
_EVENTS = load_events()
_WEIGHTS = load_deck_config()
DEFAULT_DECK = EventDeck(_EVENTS, _WEIGHTS)


def draw_event(game_state: GameState, deck: Optional[EventDeck] = None) -> Event:
    """Select a random :class:`Event` from ``deck`` and apply it."""

    deck = deck or DEFAULT_DECK
    return deck.draw(game_state)


__all__ = [
    'GameState',
    'Event',
    'EventDeck',
    'load_events',
    'load_deck_config',
    'DEFAULT_DECK',
    'draw_event',
]
