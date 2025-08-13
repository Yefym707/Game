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

from client.util_paths import user_data_dir

# Saves live inside the persistent user data directory.  ``user_data_dir``
# honours platform specific locations and mirrors the behaviour of the real
# project where configuration, logs and saves live under ``~/.oko_zombie`` (or
# ``%USERPROFILE%\\.oko_zombie`` on Windows).
SAVE_DIR = user_data_dir() / "saves"


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
    """Return ``True`` when the metadata contains the expected keys and types.

    ``Continue`` in the main menu relies on metadata validation to avoid
    launching a broken match.  The check is intentionally strict: all required
    fields must be present and of the correct type.  Additional keys are ignored
    so forward compatible saves remain loadable.
    """

    required = {"turn": int, "difficulty": str, "seed": int}
    for key, typ in required.items():
        if key not in meta or not isinstance(meta[key], typ):
            return False
    return True


def validate(slot: int) -> bool:
    """Return ``True`` if ``slot`` contains a structurally valid save file.

    Only the metadata section is inspected which keeps the check fast and
    allows callers to guard the ``Continue`` menu option without loading the
    full save file.  Any exception during parsing simply marks the slot as
    invalid.
    """

    try:
        path = _slot_path(slot)
        with path.open("r", encoding="utf-8") as fh:
            data = json.load(fh)
    except Exception:
        return False
    meta = data.get("meta", {})
    return _validate_meta(meta)


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
    "validate",
    "load",
    "save",
    "last_slot",
]

