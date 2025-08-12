"""Random events triggered at the start of a turn."""
from __future__ import annotations

import json
import random
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List

from . import entities

DATA_PATH = Path(__file__).resolve().parents[2] / "data" / "events.json"


@dataclass
class Effect:
    text_key: str
    hp: int = 0
    add_item: str | None = None
    remove_item: str | None = None
    spawn_zombies: int = 0


@dataclass
class Event:
    id: str
    icon: str
    title_key: str
    desc_key: str
    conditions: Dict[str, Any]
    effects: List[Effect]


def load_events(path: str | Path = DATA_PATH) -> List[Event]:
    """Load event definitions from JSON file."""

    path = Path(path)
    with path.open("r", encoding="utf-8") as fh:
        data = json.load(fh)
    events: List[Event] = []
    for item in data:
        effects = [
            Effect(
                e.get("text_key", "event_ok"),
                e.get("hp", 0),
                e.get("add_item"),
                e.get("remove_item"),
                e.get("spawn_zombies", 0),
            )
            for e in item.get("effects", [])
        ]
        events.append(
            Event(
                item["id"],
                item.get("icon", "?"),
                item["title_key"],
                item["desc_key"],
                item.get("conditions", {}),
                effects,
            )
        )
    return events


_EVENTS: List[Event] | None = None


def _events() -> List[Event]:
    global _EVENTS
    if _EVENTS is None:
        _EVENTS = load_events()
    return _EVENTS


def _check_conditions(state, cond: Dict[str, Any]) -> bool:
    day = state.turn
    player = state.current
    if (m := cond.get("min_day")) is not None and day < m:
        return False
    if (m := cond.get("max_day")) is not None and day > m:
        return False
    if (m := cond.get("min_hp")) is not None and player.health < m:
        return False
    if (m := cond.get("max_hp")) is not None and player.health > m:
        return False
    if (itm := cond.get("has_item")) and itm not in player.inventory:
        return False
    if (itm := cond.get("missing_item")) and itm in player.inventory:
        return False
    return True


def maybe_trigger(state, balance: Dict[str, Any]) -> Event | None:
    """Return an event that should trigger this turn, if any."""

    chance = balance.get("events", {}).get("chance", 0.0)
    if random.random() >= chance:
        return None
    for ev in _events():
        if _check_conditions(state, ev.conditions):
            return ev
    return None


def apply_effect(state, effect: Effect) -> None:
    """Apply ``effect`` to the current player and game state."""

    player = state.current
    if effect.hp:
        player.health += effect.hp
    if effect.add_item:
        player.inventory.append(effect.add_item)
    if effect.remove_item and effect.remove_item in player.inventory:
        player.inventory.remove(effect.remove_item)
    if effect.spawn_zombies:
        for _ in range(effect.spawn_zombies):
            state.zombies.append(entities.Zombie(player.x, player.y, "Z"))
