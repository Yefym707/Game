from __future__ import annotations

from enum import Enum, auto
from typing import Dict, Tuple

from .rng import RNG

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


class Difficulty(Enum):
    EASY = auto()
    NORMAL = auto()
    HARD = auto()


DIFFICULTY_PRESETS = {
    Difficulty.EASY: {"agro": 0.75, "loot": 1.25, "damage": 0.75, "spawn": 0.75},
    Difficulty.NORMAL: {"agro": 1.0, "loot": 1.0, "damage": 1.0, "spawn": 1.0},
    Difficulty.HARD: {"agro": 1.25, "loot": 0.75, "damage": 1.25, "spawn": 1.25},
}

CURRENT_DIFFICULTY = Difficulty.NORMAL

# single deterministic RNG ---------------------------------------------------
RNG = RNG()

# simple monotonically increasing identifiers used by the replay system
_TICK_COUNTER = 0
_EVENT_ID = 0

DIRECTIONS: Dict[str, Tuple[int, int]] = {
    "w": (0, -1),
    "s": (0, 1),
    "a": (-1, 0),
    "d": (1, 0),
    "q": (-1, -1),
    "e": (1, -1),
    "z": (-1, 1),
    "c": (1, 1),
}

def set_seed(seed: int) -> None:
    RNG.seed(seed)


def set_difficulty(diff: Difficulty) -> None:
    """Select active difficulty preset."""

    global CURRENT_DIFFICULTY
    CURRENT_DIFFICULTY = diff


def difficulty_preset() -> Dict[str, float]:
    return DIFFICULTY_PRESETS[CURRENT_DIFFICULTY]


def validate_action(state, action, player_index: int) -> bool:
    """Placeholder hook for server-side action validation.

    The real game logic would inspect ``state`` and ``action`` to ensure the
    move is legal for the active player.  For now the function only returns
    ``True`` to indicate that all actions are accepted.
    """

    return True


def next_tick() -> int:
    """Return the next global tick identifier."""

    global _TICK_COUNTER
    _TICK_COUNTER += 1
    return _TICK_COUNTER


def next_event_id() -> int:
    """Return a unique event id."""

    global _EVENT_ID
    _EVENT_ID += 1
    return _EVENT_ID
