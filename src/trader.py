"""Simple merchant NPC that can buy and sell items to the player.

This module provides a small :class:`Trader` class which represents a non
player character that keeps its own :class:`~inventory.Inventory` of items and
coins.  It exposes two high level methods, :meth:`buy` and :meth:`sell`, which
allow a :class:`~player.Player` to trade items for coins.  The implementation is
light‑weight but intentionally mirrors the API of :class:`Inventory` so it can
easily integrate with the rest of the project.
"""

from __future__ import annotations

from typing import Any, Dict, Optional

from inventory import Inventory


class Trader:
    """Merchant with an inventory and a list of prices.

    Parameters
    ----------
    name:
        Display name of the trader.
    goods:
        Mapping describing the initial stock.  The mapping may contain entries
        in the form ``{"item": (price, quantity)}``.  For backwards
        compatibility ``int`` values are treated as the price with a quantity of
        one and dictionaries with ``price``/``quantity`` keys are also
        understood.  Only the price information is kept – the quantities are
        inserted into the internal :class:`Inventory`.
    coins:
        Amount of coins the trader starts with.
    """

    def __init__(
        self,
        name: str,
        goods: Optional[Dict[str, Any]] = None,
        coins: int = 0,
    ) -> None:
        self.name = name
        self.inventory = Inventory(coins=coins)
        # Mapping of item name to its price in coins.
        self.prices: Dict[str, int] = {}

        if goods:
            for item, data in goods.items():
                price: int
                quantity: int
                if isinstance(data, (tuple, list)):
                    price = int(data[0])
                    quantity = int(data[1]) if len(data) > 1 else 1
                elif isinstance(data, dict):
                    price = int(
                        data.get("price")
                        or data.get("sell")
                        or data.get("buy")
                        or 0
                    )
                    quantity = int(
                        data.get("quantity")
                        or data.get("qty")
                        or 0
                    )
                else:  # assume a bare price
                    price = int(data)
                    quantity = 1

                self.prices[item] = price
                if quantity > 0:
                    self.inventory.add_item(item, quantity)

    # ------------------------------------------------------------------
    # trading helpers
    def buy(self, item_name: str, quantity: int, player: "Player") -> bool:
        """Let the ``player`` buy ``quantity`` of ``item_name``.

        The trade succeeds if the trader has enough stock and the player can
        afford the price.  Items and coins are moved between the respective
        inventories.  ``True`` is returned on success, ``False`` otherwise."""

        if quantity <= 0:
            raise ValueError("quantity must be positive")

        price = self.prices.get(item_name)
        if price is None:
            return False
        if not self.inventory.has_item(item_name, quantity):
            return False

        total = price * quantity
        if not player.inventory.spend_coins(total):
            return False

        # transfer items and coins
        self.inventory.remove_item(item_name, quantity)
        player.inventory.add_item(item_name, quantity)
        self.inventory.add_coins(total)
        return True

    def sell(self, item_name: str, quantity: int, player: "Player") -> bool:
        """Buy ``quantity`` of ``item_name`` from ``player``.

        The trade succeeds if the player owns the items and the trader has
        enough coins to pay for them.  Coins and items are exchanged between the
        two inventories.  ``True`` is returned on success."""

        if quantity <= 0:
            raise ValueError("quantity must be positive")

        price = self.prices.get(item_name)
        if price is None:
            return False

        total = price * quantity
        if self.inventory.coins < total:
            return False
        if not player.inventory.has_item(item_name, quantity):
            return False

        player.inventory.remove_item(item_name, quantity)
        player.inventory.add_coins(total)
        self.inventory.add_item(item_name, quantity)
        self.inventory.spend_coins(total)
        return True

    # ------------------------------------------------------------------
    # serialisation helpers
    def to_dict(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "prices": dict(self.prices),
            "inventory": self.inventory.to_dict(),
        }

    @staticmethod
    def from_dict(data: Dict[str, Any]) -> "Trader":
        trader = Trader(data.get("name", "Trader"), data.get("prices", {}))
        inv = data.get("inventory")
        if inv:
            trader.inventory = Inventory.from_dict(inv)
        return trader


# ``Player`` is only required for type checking.  Importing at the end avoids
# circular import issues during module initialisation.
from player import Player  # noqa  E402  (import at end of file)

