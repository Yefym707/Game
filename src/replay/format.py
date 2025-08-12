"""Replay file format description."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict

FORMAT_VERSION = 2


def make_header(game_build: str = "dev", protocol_version: int = 1, signature: str | None = None) -> Dict[str, Any]:
    """Return a minimal header describing the replay file."""

    return {
        "format_version": FORMAT_VERSION,
        "game_build": game_build,
        "protocol_version": protocol_version,
        "signature": signature,
    }


@dataclass
class Meta:
    seed: int
    mode: str
    map_id: str | None = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "seed": self.seed,
            "mode": self.mode,
            "map_id": self.map_id,
        }
