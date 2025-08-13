from __future__ import annotations

from enum import IntEnum, auto


class Layer(IntEnum):
    """Render layers ordered back to front.

    The enumeration is intentionally small and stable so that other modules can
    reference ``Layer.BG`` through ``Layer.UI`` without importing heavy
    rendering code.
    """

    BG = 0
    TILES = auto()
    ENTITIES = auto()
    OVERLAY = auto()
    UI = auto()

    # Backward compatibility -------------------------------------------------
    BACKGROUND = BG
    TILE = TILES
    ENTITY = ENTITIES
