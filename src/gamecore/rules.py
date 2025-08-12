from __future__ import annotations

import random
from enum import Enum, auto
from typing import Dict, Tuple

BOARD_SIZE = 10
STARTING_ZOMBIES = 3
MAX_TURNS = 100


class GameMode(Enum):
    """Supported game modes."""

    SOLO = auto()
    LOCAL_COOP = auto()
    ONLINE = auto()


class TurnStatus(Enum):
    """Phases during a single round."""

    PLAYER = auto()
    ZOMBIE = auto()

RNG = random.Random()

DIRECTIONS: Dict[str, Tuple[int, int]] = {
    "w": (0, -1),
    "s": (0, 1),
    "a": (-1, 0),
    "d": (1, 0),
}

def set_seed(seed: int) -> None:
    RNG.seed(seed)
