"""Balance loading and validation."""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict

from . import rules

# Default path to balance.json inside project data folder
DATA_PATH = Path(__file__).resolve().parents[2] / "data" / "balance.json"


def _check_number(name: str, value: Any, min_val: float, max_val: float) -> None:
    """Validate that ``value`` is a number within ``min_val``..``max_val``."""
    if not isinstance(value, (int, float)):
        raise ValueError(f"{name} is not a number")
    if not (min_val <= float(value) <= max_val):
        raise ValueError(f"{name} out of range")


def _validate(data: Dict[str, Any]) -> None:
    if not isinstance(data, dict):
        raise ValueError("balance must be an object")
    player = data.get("player", {})
    zombie = data.get("zombie", {})
    _check_number("player.hp", player.get("hp"), 1, 10_000)
    _check_number("player.damage", player.get("damage"), 0, 10_000)
    _check_number("zombie.hp", zombie.get("hp"), 1, 10_000)
    _check_number("zombie.damage", zombie.get("damage"), 0, 10_000)
    _check_number("zombie.agro_range", zombie.get("agro_range"), 0, 1_000)
    _check_number("zombie.limit", zombie.get("limit"), 0, 1_000)
    loot = data.get("loot", {})
    if not isinstance(loot, dict):
        raise ValueError("loot must be dict")
    for key, val in loot.items():
        _check_number(f"loot.{key}", val, 0.0, 1.0)


def load_balance(path: str | Path = DATA_PATH) -> Dict[str, Any]:
    """Load and validate balance configuration from ``path``."""
    path = Path(path)
    with path.open("r", encoding="utf-8") as fh:
        data = json.load(fh)
    _validate(data)
    preset = rules.difficulty_preset()
    # apply multipliers
    data["zombie"]["agro_range"] *= preset.get("agro", 1.0)
    data["player"]["damage"] *= preset.get("damage", 1.0)
    data["zombie"]["limit"] *= preset.get("spawn", 1.0)
    for key in data.get("loot", {}):
        data["loot"][key] = max(0.0, min(1.0, data["loot"][key] * preset.get("loot", 1.0)))
    return data
