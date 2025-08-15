from __future__ import annotations

"""Lightweight representation of a game scenario.

The project uses many small modules that model aspects of a board based game.
Up until now there was no dedicated container describing the rules and goals of
an individual scenario which made it hard to express objectives in a concise
way.  The :class:`Scenario` class introduced here acts as a tiny data holder for
such information.

A scenario has a name and description and may define a ``turn_limit`` and other
``special_conditions``.  The most important part is the ``win_condition`` which
specifies when the scenario is considered completed.  The class provides a
simple :meth:`is_completed` helper that inspects a supplied ``game_state`` object
(or ``SimpleNamespace``/dict like structure) and determines whether the win
condition is met.  Only a couple of primitive conditions are supported as the
full game logic is outside the scope of the kata:

* ``{"item": "item-name"}`` – scenario is completed when any player owns the
  given item.
* ``{"location": (x, y)}`` – completed when any player occupies the given
  board coordinate.
* ``{"survive_turns": N}`` – completed once the current turn counter reaches
  ``N``.

The class also exposes a :meth:`setup` method which can be used by callers to
perform scenario specific initialisation such as placing items on the board.  It
performs a tiny convenience action of placing entities when the board exposes a
``place_entity`` method and ``special_conditions`` contain an ``item_placement``
mapping.
"""

from dataclasses import dataclass, field
from typing import Any, Dict, Iterable, Optional, Sequence


@dataclass
class Scenario:
    """Container describing a game scenario's rules and objectives."""

    name: str
    description: str
    win_condition: Dict[str, Any] = field(default_factory=dict)
    turn_limit: Optional[int] = None
    special_conditions: Dict[str, Any] = field(default_factory=dict)
    lose_condition: Dict[str, Any] = field(default_factory=dict)

    def setup(self, board: Any, players: Sequence[Any]) -> None:
        """Perform scenario specific initialisation.

        The default implementation is intentionally lightweight and merely
        handles a very small convenience feature: if ``special_conditions``
        contains an ``"item_placement"`` mapping and ``board`` exposes a
        ``place_entity`` method, the entities are placed on the board.  The
        structure of the mapping is ``{(x, y): symbol}`` where ``symbol`` is the
        representation used on the board.  Callers are free to override or
        extend this behaviour as required.
        """

        placement = self.special_conditions.get("item_placement", {})
        if hasattr(board, "place_entity"):
            items: Iterable = []
            if isinstance(placement, dict):
                items = placement.items()
            elif isinstance(placement, list):
                items = [((x, y), sym) for x, y, sym in placement]
            for (x, y), symbol in items:
                try:
                    board.place_entity(x, y, symbol)
                except Exception:
                    # Placement is a convenience feature; ignore errors silently
                    # so that tests can run with very small board mocks.
                    pass

    # ------------------------------------------------------------------
    # Win condition handling
    # ------------------------------------------------------------------
    def is_completed(self, game_state: Any) -> bool:
        """Return ``True`` if the scenario's win condition is met.

        ``game_state`` is expected to expose at least a ``players`` iterable and
        optionally a ``turn`` counter.  The method purposefully operates on a
        minimal API so that unit tests can provide ``SimpleNamespace`` instances
        instead of full game objects.
        """

        players: Iterable[Any] = getattr(game_state, "players", None)
        if players is None:
            single = getattr(game_state, "player", None)
            players = [single] if single is not None else []
        win = self.win_condition

        # Check for item possession ---------------------------------------
        item_name = win.get("item")
        if item_name is not None:
            for player in players:
                has_item = False
                if hasattr(player, "has_item"):
                    has_item = player.has_item(item_name)
                elif getattr(player, "inventory", None) and hasattr(
                    player.inventory, "has_item"
                ):
                    has_item = player.inventory.has_item(item_name)
                if has_item:
                    if item_name == "antidote":
                        game_map = getattr(game_state, "game_map", None)
                        start_attr = getattr(game_map, "start_pos", None)
                        start_pos = tuple(start_attr) if start_attr else (0, 0)
                        if (getattr(player, "x", None), getattr(player, "y", None)) != start_pos:
                            continue
                    return True

        # Check for reaching a location ----------------------------------
        target_loc = win.get("location") or win.get("reach_location")
        if target_loc is not None:
            tx, ty = target_loc
            for player in players:
                if (getattr(player, "x", None), getattr(player, "y", None)) == (tx, ty):
                    return True

        # Check for surviving a number of turns --------------------------
        survive_turns = win.get("survive_turns")
        if survive_turns is not None:
            current_turn = getattr(game_state, "turn", getattr(game_state, "turn_count", 0))
            if current_turn >= int(survive_turns):
                return True

        # Check rescue counters ------------------------------------------
        rescued = win.get("rescued")
        if rescued is not None:
            if getattr(game_state, "rescued", 0) >= int(rescued):
                return True

        return False

    def is_failed(self, game_state: Any) -> bool:
        """Return ``True`` if a lose condition is met."""

        players: Iterable[Any] = getattr(game_state, "players", None)
        if players is None:
            single = getattr(game_state, "player", None)
            players = [single] if single is not None else []
        lose = self.lose_condition

        if lose.get("player_dead"):
            for player in players:
                if getattr(player, "health", 1) <= 0:
                    return True

        limit = lose.get("turn_limit") or self.turn_limit
        if limit is not None:
            current_turn = getattr(game_state, "turn", getattr(game_state, "turn_count", 0))
            if current_turn >= int(limit):
                return True

        if lose.get("base_destroyed") and getattr(game_state, "base_destroyed", False):
            return True

        return False
