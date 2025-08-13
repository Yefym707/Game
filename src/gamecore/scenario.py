"""Scenario loading helper."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, List

DATA_FILE = Path(__file__).resolve().parents[2] / "data" / "scenarios.json"
DEFAULT_SCENARIOS = [{"id": "default", "name": "Default"}]


def load_scenarios(path: Path = DATA_FILE) -> List[Dict[str, Any]]:
    try:
        with path.open("r", encoding="utf-8") as fh:
            return json.load(fh)
    except FileNotFoundError:
        return list(DEFAULT_SCENARIOS)


__all__ = ["load_scenarios"]

