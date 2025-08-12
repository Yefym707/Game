"""Scenario loading and application."""
from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List

from . import board as gboard, rules

DATA_PATH = Path(__file__).resolve().parents[2] / "data" / "scenarios.json"
ROOT_DIR = Path(__file__).resolve().parents[2]


@dataclass
class Scenario:
    id: str
    name_key: str
    map_file: str
    goals: List[str]
    starting_items: List[str]
    difficulty: str


def load_scenarios(path: str | Path = DATA_PATH) -> Dict[str, Scenario]:
    """Load all scenarios from JSON."""

    path = Path(path)
    with path.open("r", encoding="utf-8") as fh:
        data = json.load(fh)
    res: Dict[str, Scenario] = {}
    for item in data:
        res[item["id"]] = Scenario(
            item["id"],
            item["name_key"],
            item.get("map_file", ""),
            item.get("goals", []),
            item.get("starting_items", []),
            item.get("difficulty", "normal"),
        )
    return res


_SCENARIOS: Dict[str, Scenario] | None = None


def _scenarios() -> Dict[str, Scenario]:
    global _SCENARIOS
    if _SCENARIOS is None:
        _SCENARIOS = load_scenarios()
    return _SCENARIOS


def get_scenario(sid: str) -> Scenario:
    return _scenarios()[sid]


def apply_scenario(state, scen: Scenario) -> None:
    """Apply ``scen`` to ``state`` setting map, items and difficulty."""

    map_path = ROOT_DIR / scen.map_file
    with map_path.open("r", encoding="utf-8") as fh:
        layout = json.load(fh)
    width = len(layout[0])
    height = len(layout)
    tiles = [list(row) for row in layout]
    state.board = gboard.Board(width, height, tiles)
    for p in state.players:
        p.inventory.extend(scen.starting_items)
    diff = rules.Difficulty[scen.difficulty.upper()]
    rules.set_difficulty(diff)
