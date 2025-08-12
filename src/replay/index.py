"""Simple in-memory index for replay events."""
from __future__ import annotations

from typing import Dict, Iterable


def build_index(events: Iterable[dict]) -> Dict[int, int]:
    """Return mapping of turn -> first event position."""

    mapping: Dict[int, int] = {}
    for pos, ev in enumerate(events):
        turn = ev.get("turn")
        if turn is not None and turn not in mapping:
            mapping[int(turn)] = pos
    return mapping
