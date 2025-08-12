from __future__ import annotations

import random
from enum import Enum, auto
from typing import Dict, Tuple

BOARD_SIZE = 10
STARTING_ZOMBIES = 3
MAX_TURNS = 100

# Demo configuration -----------------------------------------------------

# Flag toggled when the game runs in limited demo mode.  Set by the client
# when ``--demo`` is passed on the command line.
DEMO_MODE = False

# Maximum number of in-game days/turns allowed in the demo.
DEMO_MAX_DAYS = 3

# The demo ships with a single map and uses a reduced loot multiplier.  The
# actual systems consuming these values are free to interpret them as needed.
DEMO_MAX_MAPS = 1
DEMO_LOOT_FACTOR = 0.5


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


def validate_action(state, action, player_index: int) -> bool:
    """Placeholder hook for server-side action validation.

    The real game logic would inspect ``state`` and ``action`` to ensure the
    move is legal for the active player.  For now the function only returns
    ``True`` to indicate that all actions are accepted.
    """

    return True
