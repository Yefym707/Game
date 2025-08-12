from __future__ import annotations

from typing import Any, Callable, Dict

# Mapping from a save version to the function that migrates the
# payload to the next version.
MIGRATIONS: Dict[int, Callable[[Dict[str, Any]], Dict[str, Any]]] = {}


def migrate_v1_to_v2(data: Dict[str, Any]) -> Dict[str, Any]:
    """Upgrade version 1 saves to version 2 format.

    Version 1 used a single ``player`` entry and lacked an explicit
    game mode.  Version 2 expects a list of ``players`` and stores the
    mode separately.  This function performs a deterministic and pure
    transformation without mutating the input ``data``.
    """

    player = data.get("player", {})
    new_data = {
        "save_version": 2,
        "mode": "SOLO",
        "players": [player],
        "state": data.get("state", {}),
    }
    return new_data


MIGRATIONS[1] = migrate_v1_to_v2


def apply_migrations(data: Dict[str, Any], target_version: int) -> Dict[str, Any]:
    """Apply migration functions until ``target_version`` is reached."""

    version = data.get("save_version", 1)
    while version < target_version:
        func = MIGRATIONS.get(version)
        if not func:
            raise ValueError(f"No migration available for save version {version}")
        data = func(data)
        version = data.get("save_version", version + 1)
    return data
