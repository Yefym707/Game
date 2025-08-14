from __future__ import annotations

"""Simple achievement tracking system.

The tracker is notified about relevant game events and unlocks achievements
when their conditions are met.  For now achievements are merely printed to the
console, but :func:`unlock_achievement` is structured in a way so it can later
be extended to integrate with the Steamworks API or similar services.
"""

from typing import Callable, Set

# ---------------------------------------------------------------------------
# Achievement identifiers
FIRST_BLOOD = "First Blood"
ZOMBIE_SLAYER = "Zombie Slayer"
SURVIVOR = "Survivor"


class AchievementTracker:
    """Track and unlock achievements based on game events.

    Parameters
    ----------
    notifier:
        Optional callback that receives the name of an unlocked achievement.
        When omitted a simple ``print`` based notifier is used.
    """

    def __init__(self, notifier: Callable[[str], None] | None = None) -> None:
        self._notifier = notifier or (lambda name: print(f"Achievement Unlocked: {name}"))
        self._unlocked: Set[str] = set()
        self.zombie_kills: int = 0
        self.players_dead: int = 0

    # ------------------------------------------------------------------
    # helpers
    def unlock_achievement(self, name: str) -> None:
        """Mark ``name`` as unlocked and notify once.

        This function is the central place where integration with external
        achievement providers would occur.
        """

        if name in self._unlocked:
            return
        self._unlocked.add(name)
        self._notifier(name)

    def is_unlocked(self, name: str) -> bool:
        """Return ``True`` if ``name`` has already been unlocked."""

        return name in self._unlocked

    # ------------------------------------------------------------------
    # event handlers
    def on_zombie_kill(self) -> None:
        """Handle the event of a zombie being killed."""

        self.zombie_kills += 1
        if self.zombie_kills == 1:
            self.unlock_achievement(FIRST_BLOOD)
        if self.zombie_kills >= 50:
            self.unlock_achievement(ZOMBIE_SLAYER)

    def on_player_death(self) -> None:
        """Record that a player has died in the current scenario."""

        self.players_dead += 1

    def on_scenario_win(self) -> None:
        """Handle the event of winning a scenario.

        The ``SURVIVOR`` achievement is unlocked if no players died during the
        scenario.  Player death counters are reset afterwards.
        """

        if self.players_dead == 0:
            self.unlock_achievement(SURVIVOR)
        self.players_dead = 0

    # ------------------------------------------------------------------
    def reset(self) -> None:
        """Reset all internal counters and unlocked achievements."""

        self.zombie_kills = 0
        self.players_dead = 0
        self._unlocked.clear()
