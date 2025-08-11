from __future__ import annotations

import json
import gzip
from pathlib import Path
from typing import Any

from . import board

SAVE_VERSION = 1


def save_game(state: board.GameState, path: str | Path) -> None:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    data = {"save_version": SAVE_VERSION, "state": state.to_dict()}
    text = json.dumps(data)
    if path.suffix == ".gz":
        with gzip.open(path, "wt", encoding="utf-8") as fh:
            fh.write(text)
    else:
        with path.open("w", encoding="utf-8") as fh:
            fh.write(text)


def load_game(path: str | Path) -> board.GameState:
    path = Path(path)
    if path.suffix == ".gz":
        with gzip.open(path, "rt", encoding="utf-8") as fh:
            data = json.load(fh)
    else:
        with path.open("r", encoding="utf-8") as fh:
            data = json.load(fh)
    if data.get("save_version") != SAVE_VERSION:
        raise ValueError("Unsupported save version")
    return board.GameState.from_dict(data["state"])
