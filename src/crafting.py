"""Utilities for loading crafting recipes and performing simple crafting.

The original project supports a JSON-based recipe system.  For unit tests and
examples we also expose a very small in-memory recipe table together with a
utility function :func:`craft_item` that operates directly on a plain
inventory mapping.
"""

import json
from typing import Dict, List, Optional, Tuple


class Recipe:
    def __init__(self, name: str, ingredients: Dict[str, int], result: str, result_qty: int = 1):
        self.name = name
        self.ingredients = ingredients  # {item: qty}
        self.result = result
        self.result_qty = result_qty

    @staticmethod
    def from_dict(d: Dict[str, object]) -> "Recipe":
        return Recipe(
            name=d["name"],
            ingredients=d["ingredients"],
            result=d["result"],
            result_qty=d.get("result_qty", 1),
        )


def load_recipes(filename: str = "src/recipes.json") -> List[Recipe]:
    """Load a list of :class:`Recipe` objects from a JSON file."""

    with open(filename, "r", encoding="utf-8") as f:
        data = json.load(f)
    return [Recipe.from_dict(r) for r in data]


# ---------------------------------------------------------------------------
# Simple crafting system
# ---------------------------------------------------------------------------

# Mapping of two ingredient names to the resulting crafted item.  Keys are
# stored as sorted tuples so that the order of the ingredients does not matter
# when looking up a recipe.
RECIPES: Dict[Tuple[str, str], str] = {
    ("Gasoline", "Keys"): "Vehicle",
}


def craft_item(inventory: Dict[str, int], item1: str, item2: str) -> Optional[str]:
    """Attempt to craft a new item from ``item1`` and ``item2``.

    Parameters
    ----------
    inventory:
        Mapping of item names to their quantities.  It is modified in-place.
    item1, item2:
        Ingredient names.  The order is irrelevant.

    Returns
    -------
    str | None
        The name of the crafted item if successful, otherwise ``None``.
    """

    key = tuple(sorted((item1, item2)))
    result = RECIPES.get(key)
    if result is None:
        return None

    # Determine whether enough resources exist.  If both ingredients are the
    # same item we need at least two of them.
    if item1 == item2:
        if inventory.get(item1, 0) < 2:
            return None
        inventory[item1] -= 2
        if inventory[item1] == 0:
            del inventory[item1]
    else:
        if inventory.get(item1, 0) < 1 or inventory.get(item2, 0) < 1:
            return None
        inventory[item1] -= 1
        if inventory[item1] == 0:
            del inventory[item1]
        inventory[item2] -= 1
        if inventory[item2] == 0:
            del inventory[item2]

    inventory[result] = inventory.get(result, 0) + 1
    return result


__all__ = [
    "Recipe",
    "load_recipes",
    "RECIPES",
    "craft_item",
]

