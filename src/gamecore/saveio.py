from __future__ import annotations

import json
import gzip
from pathlib import Path
from typing import Any

from . import board, rules, entities
from integrations import steam

SAVE_VERSION = 2


def save_game(state: board.GameState, path: str | Path) -> None:
    """Persist ``state`` to ``path``.

    Network matches are intentionally not saved to disk to avoid accidental
    spoilers or cheating.  The caller can still create manual snapshots by
    serialising the state with :mod:`net.serialization` if required.
    """

    if state.mode is rules.GameMode.ONLINE:
        return
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    data = {
        "save_version": SAVE_VERSION,
        "mode": state.mode.name,
        "players": [p.to_dict() for p in state.players],
        "state": state.to_dict(),
    }
    text = json.dumps(data)
    if steam.cloud_saves:
        payload: bytes
        if path.suffix == ".gz":
            payload = gzip.compress(text.encode("utf-8"))
        else:
            payload = text.encode("utf-8")
        steam.save(path.name, payload)
    else:
        if path.suffix == ".gz":
            with gzip.open(path, "wt", encoding="utf-8") as fh:
                fh.write(text)
        else:
            with path.open("w", encoding="utf-8") as fh:
                fh.write(text)


def load_game(path: str | Path) -> board.GameState:
    path = Path(path)
    if steam.cloud_saves:
        raw = steam.load(path.name)
        if raw is None:
            raise FileNotFoundError(path.name)
        if path.suffix == ".gz":
            data = json.loads(gzip.decompress(raw).decode("utf-8"))
        else:
            data = json.loads(raw.decode("utf-8"))
    elif path.suffix == ".gz":
        with gzip.open(path, "rt", encoding="utf-8") as fh:
            data = json.load(fh)
    else:
        with path.open("r", encoding="utf-8") as fh:
            data = json.load(fh)
    if data.get("save_version") != SAVE_VERSION:
        raise ValueError("Unsupported save version")
    mode = rules.GameMode[data.get("mode", "SOLO")]
    players = [entities.Player.from_dict(p) for p in data.get("players", [])]
    return board.GameState.from_dict(data["state"], mode=mode, players=players)
