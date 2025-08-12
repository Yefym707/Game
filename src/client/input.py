from __future__ import annotations

"""Unified keyboard/gamepad input layer.

This module provides a very small abstraction for keyboard and gamepad
bindings.  It focuses on persistence of the bindings rather than on
real-time event processing which keeps the implementation lightweight and
suitable for headless unit tests.
"""

from typing import Dict, Optional

try:  # pragma: no cover - pygame may be missing in the test environment
    import pygame  # type: ignore
except Exception:  # pragma: no cover - fallback stub with minimal key constants
    class _Stub:
        K_UP = 273
        K_DOWN = 274
        K_LEFT = 276
        K_RIGHT = 275
        K_SPACE = 32
        K_r = ord("r")
        K_g = ord("g")
        K_ESCAPE = 27
        K_F5 = 0x3A
        K_F9 = 0x3E
        KEYDOWN = 2
        JOYBUTTONDOWN = 10
        joystick = type("joy", (), {"get_count": staticmethod(lambda: 0)})

    pygame = _Stub()  # type: ignore

# ---------------------------------------------------------------------------
# default bindings ----------------------------------------------------------
# ---------------------------------------------------------------------------

DEFAULT_BINDINGS: Dict[str, int] = {
    # movement of player
    "move_up": pygame.K_UP,
    "move_down": pygame.K_DOWN,
    "move_left": pygame.K_LEFT,
    "move_right": pygame.K_RIGHT,
    # actions
    "end_turn": pygame.K_SPACE,
    "rest": pygame.K_r,
    "scavenge": pygame.K_g,
    "pause": pygame.K_ESCAPE,
    "quick_save": pygame.K_F5,
    "quick_load": pygame.K_F9,
}

# Gamepad mapping uses simple button/stick ids.  The values are not used by
# the tests but are provided so that the runtime game can map controller
# input.  They correspond to the common XInput layout used by pygame.
DEFAULT_GAMEPAD: Dict[str, int] = {
    "end_turn": 0,   # A
    "pause": 7,      # Start
    "scavenge": 2,   # X
    "rest": 3,       # Y
}


class InputManager:
    """Handle action bindings and persistence.

    Parameters
    ----------
    cfg:
        Configuration dictionary returned by :mod:`gamecore.config`.
    """

    def __init__(self, cfg: Dict[str, object]):
        self.cfg = cfg
        saved = cfg.get("bindings", {})
        self.profiles: Dict[int, Dict[str, int]] = {}
        if isinstance(saved, dict) and saved and all(k.isdigit() for k in saved.keys()):
            for pid, binds in saved.items():
                self.profiles[int(pid)] = {
                    action: int(binds.get(action, key))
                    for action, key in DEFAULT_BINDINGS.items()
                }
        else:
            self.profiles[0] = {
                action: int(saved.get(action, key))
                for action, key in DEFAULT_BINDINGS.items()
            }
        self.active = 0
        self.bindings = self.profiles[self.active]
        # optional gamepad
        self.gamepad: Optional[pygame.joystick.Joystick] = None
        try:
            if pygame.joystick.get_count():
                self.gamepad = pygame.joystick.Joystick(0)
                self.gamepad.init()
        except Exception:  # pragma: no cover - joystick is optional
            self.gamepad = None

    # ------------------------------------------------------------------
    # persistence helpers
    # ------------------------------------------------------------------
    def save(self, cfg: Optional[Dict[str, object]] = None) -> None:
        """Write current bindings into ``cfg`` (default: stored cfg)."""

        target = cfg if cfg is not None else self.cfg
        target["bindings"] = {str(pid): binds for pid, binds in self.profiles.items()}

    def reset_defaults(self) -> None:
        """Reset all bindings to :data:`DEFAULT_BINDINGS`."""

        for pid in self.profiles:
            for action, key in DEFAULT_BINDINGS.items():
                self.profiles[pid][action] = key
        self.bindings = self.profiles[self.active]

    # ------------------------------------------------------------------
    # basic query interface
    # ------------------------------------------------------------------
    def rebind(self, action: str, key: int) -> None:
        """Change binding for ``action`` to ``key``."""

        if action in self.bindings:
            self.bindings[action] = int(key)

    def action_from_key(self, key: int) -> Optional[str]:
        """Return action name matching ``key`` if bound."""

        for action, k in self.bindings.items():
            if k == key:
                return action
        return None

    # ------------------------------------------------------------------
    # profile switching -------------------------------------------------
    # ------------------------------------------------------------------
    def set_profile(self, pid: int) -> None:
        """Switch to bindings for ``pid``."""

        if pid not in self.profiles:
            self.profiles[pid] = {action: key for action, key in DEFAULT_BINDINGS.items()}
        self.active = pid
        self.bindings = self.profiles[pid]


class InputState:
    """Simple structure storing currently triggered actions.

    ``process_event`` adds actions based on incoming pygame events.  The state
    is expected to be cleared by the user each frame.
    """

    def __init__(self) -> None:
        self.actions: set[str] = set()

    def process_event(self, event: pygame.event.Event, manager: InputManager) -> None:
        if event.type == pygame.KEYDOWN:
            action = manager.action_from_key(event.key)
            if action:
                self.actions.add(action)
        elif event.type == pygame.JOYBUTTONDOWN and manager.gamepad:
            # map joystick button to action
            for act, btn in DEFAULT_GAMEPAD.items():
                if event.button == btn:
                    self.actions.add(act)
                    break

    def clear(self) -> None:
        self.actions.clear()
