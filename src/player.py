"""Player entity used by the simplified campaign module.

This module originally provided only a very small ``Player`` class which kept
track of a position and a health value.  For the text based game to be useful
in unit tests a couple of additional features are required: a name, an
inventory for items and some helpers to modify the player's state.  The class
below stays intentionally lightweight but offers a convenient API that mirrors
the expectations of the surrounding code base.
"""

from __future__ import annotations

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
