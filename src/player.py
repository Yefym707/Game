"""Player entity used by the simplified campaign module.

This module originally provided only a very small ``Player`` class which kept
track of a position and a health value.  For the text based game to be useful
in unit tests a couple of additional features are required: a name, an
inventory for items and some helpers to modify the player's state.  The class
below stays intentionally lightweight but offers a convenient API that mirrors
the expectations of the surrounding code base.
"""

from __future__ import annotations

import random
from typing import Optional

from entity import Entity
from inventory import Inventory


class Player(Entity):
    """Player with a name, health and an :class:`Inventory` of items."""

    def __init__(
        self,
        x: int = 0,
        y: int = 0,
        health: int = 5,
        max_health: int = 5,
        name: str = "Hero",
        inventory: Optional[Inventory] = None,
    ) -> None:
        super().__init__(x, y, health)
        self.max_health = max_health
        self.name = name
        # Every player owns an inventory which defaults to an empty one.
        self.inventory: Inventory = inventory or Inventory()
        # representation on the board
        self.symbol: str = "P"
        # action management
        self.actions_left: int = 0
        self.turn_over: bool = False

    # ------------------------------------------------------------------
    # turn helpers
    def start_turn(self, actions: int) -> None:
        """Begin a new turn with ``actions`` available."""

        self.actions_left = max(0, actions)
        self.turn_over = False

    def end_turn(self) -> None:
        """Mark the player's turn as finished."""

        self.actions_left = 0
        self.turn_over = True

    def _use_action(self) -> None:
        """Consume a single action and end the turn if none remain."""

        if self.actions_left > 0:
            self.actions_left -= 1
            if self.actions_left <= 0:
                self.end_turn()
        else:
            # No actions to spend – immediately end the turn.
            self.end_turn()

    # ------------------------------------------------------------------
    # health helpers
    def heal(self, amount: int) -> None:
        """Increase health by ``amount`` up to ``max_health``."""

        self.health = min(self.max_health, self.health + amount)

    def take_damage(self, amount: int) -> None:
        """Reduce health by ``amount`` without going below zero."""

        self.health = max(0, self.health - max(0, amount))

    # For backwards compatibility some parts of the project still call this
    # method ``damage``.  Delegate to :meth:`take_damage` so existing tests keep
    # working.
    def damage(self, amount: int) -> None:  # pragma: no cover - thin wrapper
        self.take_damage(amount)

    # ------------------------------------------------------------------
    # inventory helpers
    def pick_up(self, item_name: str, quantity: int = 1) -> None:
        """Add ``quantity`` of ``item_name`` to the inventory."""

        self.inventory.add_item(item_name, quantity)

    def drop_item(self, item_name: str, quantity: int = 1) -> None:
        """Remove ``quantity`` of ``item_name`` from the inventory."""

        self.inventory.remove_item(item_name, quantity)

    def has_item(self, item_name: str, quantity: int = 1) -> bool:
        """Return ``True`` if at least ``quantity`` of ``item_name`` is held."""

        return self.inventory.has_item(item_name, quantity)

    # ------------------------------------------------------------------
    # action helpers
    def move(self, dx: int, dy: int, game_board) -> bool:
        """Move by ``(dx, dy)`` on ``game_board`` if possible.

        Returns ``True`` if the move was successful.  Moving consumes one
        action.  The board is updated to reflect the new position.  Attempts to
        move without available actions or into blocked/out-of-bounds tiles fail
        without consuming an action.
        """

        if self.actions_left <= 0:
            self.end_turn()
            return False

        new_x = self.x + dx
        new_y = self.y + dy
        if not game_board.is_tile_free(new_x, new_y):
            return False

        # update board and position
        try:
            game_board.remove_entity(self.x, self.y)
        except ValueError:
            pass
        game_board.place_entity(new_x, new_y, self.symbol)
        self.set_position(new_x, new_y)
        self._use_action()
        return True

    def attack(self, target) -> bool:
        """Attack an adjacent ``target`` reducing its health by one.

        Returns ``True`` if the attack was executed.  The attack consumes one
        action.  The ``target`` is expected to expose ``take_damage`` or
        ``damage`` methods.  If the target's health drops to zero or below it is
        considered defeated.
        """

        if self.actions_left <= 0:
            self.end_turn()
            return False

        if abs(self.x - target.x) + abs(self.y - target.y) != 1:
            return False

        if hasattr(target, "take_damage"):
            target.take_damage(1)
        elif hasattr(target, "damage"):
            target.damage(1)
        else:  # pragma: no cover - defensive
            target.health = max(0, target.health - 1)

        self._use_action()
        return True

    def search(self, game_board) -> Optional[str]:
        """Search the current tile for items.

        If the board exposes an ``items`` mapping it is checked for a supply
        token at the player's position.  Otherwise there is a small random
        chance to find a ``"supply"``.  Found items are added to the player's
        inventory and removed from the board.  Searching consumes one action.

        Returns the name of the item found or ``None`` if nothing was
        discovered.
        """

        if self.actions_left <= 0:
            self.end_turn()
            return None

        found = None

        items = getattr(game_board, "items", None)
        if items is not None:
            found = items.pop((self.x, self.y), None)

        if found is None and random.random() < 0.2:
            found = "supply"

        if found is not None:
            self.pick_up(found)

        self._use_action()
        return found

    # ------------------------------------------------------------------
    # serialisation helpers
    def to_dict(self) -> dict:
        return {
            "x": self.x,
            "y": self.y,
            "health": self.health,
            "max_health": self.max_health,
            "name": self.name,
            "inventory": self.inventory.to_dict(),
        }

    @staticmethod
    def from_dict(d: dict) -> "Player":
        return Player(
            x=d.get("x", 0),
            y=d.get("y", 0),
            health=d.get("health", 5),
            max_health=d.get("max_health", d.get("health", 5)),
            name=d.get("name", "Hero"),
            inventory=Inventory.from_dict(d.get("inventory", {})),
        )
