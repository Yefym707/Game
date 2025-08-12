"""Replay file reader and basic timeline navigation."""
from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Dict, Any

from . import storage
from . import index
from gamecore import saveio
from net.attestation import hmac_sign


class Player:
    def __init__(self, path: str | Path) -> None:
        self.path = Path(path)
        self.header: Dict[str, Any] = {}
        self.meta: Dict[str, Any] = {}
        self.events: list[Dict[str, Any]] = []
        self.checkpoints: Dict[int, Dict[str, Any]] = {}
        self.rate = 1.0

    @classmethod
    def load(cls, path: str | Path) -> "Player":
        """Load ``path`` verifying optional HMAC signatures."""

        player = cls(path)
        key = os.environ.get("REPLAY_HMAC_KEY")
        with storage.open_read(path) as fh:
            lines = fh.readlines()
        if lines and "signature" in lines[-1]:
            sig = json.loads(lines.pop())  # remove signature line
            signature = sig.get("signature")
            if key and signature:
                data = "".join(lines).encode("utf-8")
                if hmac_sign(data, key.encode()) != signature:
                    raise ValueError("bad signature")
        if len(lines) >= 1:
            player.header = json.loads(lines[0])
        if len(lines) >= 2:
            player.meta = json.loads(lines[1])
        for line in lines[2:]:
            data = json.loads(line)
            player.events.append(data)
            if data.get("type") == "CHECKPOINT":
                player.checkpoints[int(data["turn"])] = data["state"]
        player._index = index.build_index(player.events)
        return player

    def seek(self, turn: int):
        """Return game state at ``turn`` using nearest checkpoint."""

        available = [t for t in self.checkpoints if t <= turn]
        if not available:
            raise ValueError("No checkpoint available")
        chk_turn = max(available)
        snap = self.checkpoints[chk_turn]
        state = saveio.restore(snap)
        return state

    def step_forward(self):
        pass  # CONTINUE

    def step_back(self):
        pass  # CONTINUE

    def set_rate(self, rate: float) -> None:
        self.rate = rate
