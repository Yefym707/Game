from __future__ import annotations

from enum import IntEnum, auto


class Layer(IntEnum):
    """Render layers ordered back to front."""

    BG = 0
    TILES = auto()
    ENTITIES = auto()
    OVERLAY = auto()
    UI = auto()

    # Backward compatibility -------------------------------------------------
    BACKGROUND = BG
    TILE = TILES
    ENTITY = ENTITIES
