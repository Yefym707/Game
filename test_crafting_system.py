import os
import sys


sys.path.append(os.path.join(os.path.dirname(__file__), "src"))

from crafting import RECIPES, craft_item


def test_craft_vehicle_success_and_order_irrelevant():
    inventory = {"Gasoline": 1, "Keys": 1}

    # Order of ingredients should not matter
    result = craft_item(inventory, "Keys", "Gasoline")

    assert result == "Vehicle"
    assert inventory == {"Vehicle": 1}


def test_craft_fails_for_missing_or_invalid():
    inventory = {"Gasoline": 1}

    result = craft_item(inventory, "Gasoline", "Keys")

    assert result is None
    # Inventory should remain unchanged
    assert inventory == {"Gasoline": 1}

