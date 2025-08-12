from __future__ import annotations

from enum import IntEnum, auto


class Layer(IntEnum):
    BACKGROUND = 0
    TILE = auto()
    ENTITY = auto()
    OVERLAY = auto()
    UI = auto()
