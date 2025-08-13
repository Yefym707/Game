"""Save file helpers.

The real project exposes a fairly feature rich save subsystem with cloud
integration and migrations.  For the tests in this kata we only require a
light‑weight wrapper that lists, reads and writes JSON files.  The helpers below
mirror the behaviour expected by the unit tests: saves are written atomically
and metadata is validated strictly so the ``Continue`` option never starts a
broken game.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, List

from . import config

SAVE_DIR = config.CONFIG_DIR / "saves"


def _slot_path(slot: int) -> Path:
    return SAVE_DIR / f"{slot}.json"


def list_saves() -> List[Dict[str, Any]]:
    """Return metadata for all save slots."""

    SAVE_DIR.mkdir(parents=True, exist_ok=True)
    saves: List[Dict[str, Any]] = []
    for path in SAVE_DIR.glob("*.json"):
        try:
            with path.open("r", encoding="utf-8") as fh:
                data = json.load(fh)
            saves.append({"slot": int(path.stem), "meta": data.get("meta", {})})
        except Exception:
            continue
    return sorted(saves, key=lambda s: s["slot"])


def find_last_save() -> int | None:
    saves = list_saves()
    if not saves:
        return None
    return max(s["slot"] for s in saves)


def _validate_meta(meta: Dict[str, Any]) -> bool:
    """Return ``True`` if ``meta`` contains the required fields."""

    required = {"turn", "difficulty", "seed"}
    return required.issubset(meta.keys())


def load(slot: int) -> Dict[str, Any]:
    path = _slot_path(slot)
    with path.open("r", encoding="utf-8") as fh:
        data = json.load(fh)
    meta = data.get("meta", {})
    if not _validate_meta(meta):
        raise ValueError("invalid metadata")
    return data


def save(slot: int, data: Dict[str, Any]) -> None:
    """Atomically store ``data`` in ``slot``."""

    SAVE_DIR.mkdir(parents=True, exist_ok=True)
    path = _slot_path(slot)
    tmp = path.with_suffix(".tmp")
    with tmp.open("w", encoding="utf-8") as fh:
        json.dump(data, fh)
    tmp.replace(path)


# backward compatible helper used in tests -----------------------------------
last_slot = find_last_save


__all__ = [
    "list_saves",
    "find_last_save",
    "load",
    "save",
    "last_slot",
]

