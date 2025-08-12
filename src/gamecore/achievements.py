from __future__ import annotations

"""Simple achievement tracking hooked into ``steamwrap``.

The implementation keeps track of a couple of counters and forwards unlocked
achievements to :mod:`integrations.steamwrap`.  In tests a fake steam wrapper
can be supplied via :func:`init`.
"""

from typing import Iterable, Tuple

from integrations import steam as _steam_default

# Achievement identifiers -------------------------------------------------
ACH_WIN_CAMPAIGN = "ACH_WIN_CAMPAIGN"
ACH_KILL_100 = "ACH_KILL_100_ZOMBIES"
ACH_FOUR_PLAYERS = "ACH_FOUR_PLAYERS"
ACH_WIN_NO_DAMAGE = "ACH_WIN_NO_DAMAGE"

_steam = _steam_default
_kill_count = 0
_no_damage = True


def init(wrapper=_steam_default) -> None:
    """Initialise the module with a specific steam wrapper."""

    global _steam
    _steam = wrapper
    reset()


def reset() -> None:
    global _kill_count, _no_damage
    _kill_count = 0
    _no_damage = True


def on_game_start(players: int) -> None:
    """Call when a new game starts."""

    reset()
    if players >= 4:
        _steam.set_achievement(ACH_FOUR_PLAYERS)
        _steam.store_stats()


def on_zombie_kill() -> None:
    global _kill_count
    _kill_count += 1
    if _kill_count >= 100:
        _steam.set_achievement(ACH_KILL_100)
        _steam.store_stats()


def on_player_damage() -> None:
    global _no_damage
    _no_damage = False


def on_campaign_win() -> None:
    _steam.set_achievement(ACH_WIN_CAMPAIGN)
    if _no_damage:
        _steam.set_achievement(ACH_WIN_NO_DAMAGE)
    _steam.store_stats()
    reset()


def list_achievements() -> Iterable[Tuple[str, bool]]:
    """Return all achievement ids with unlocked state."""

    ids = [ACH_WIN_CAMPAIGN, ACH_KILL_100, ACH_FOUR_PLAYERS, ACH_WIN_NO_DAMAGE]
    return [(aid, _steam.is_achievement_unlocked(aid)) for aid in ids]
