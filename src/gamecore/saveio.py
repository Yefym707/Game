from __future__ import annotations

import json
import gzip
from typing import Any

from . import board

VERSION = 1


def save_game(state: board.GameState, path: str) -> None:
    path = str(path)
    data = {"version": VERSION, "state": state.to_dict()}
    text = json.dumps(data)
    if path.endswith(".gz"):
        with gzip.open(path, "wt", encoding="utf-8") as fh:
            fh.write(text)
    else:
        with open(path, "w", encoding="utf-8") as fh:
            fh.write(text)


def load_game(path: str) -> board.GameState:
    path = str(path)
    if path.endswith(".gz"):
        with gzip.open(path, "rt", encoding="utf-8") as fh:
            data = json.load(fh)
    else:
        with open(path, "r", encoding="utf-8") as fh:
            data = json.load(fh)
    if data.get("version") != VERSION:
        raise ValueError("Unsupported save version")
    return board.GameState.from_dict(data["state"])
