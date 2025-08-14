import os
import sys


sys.path.append(os.path.join(os.path.dirname(__file__), "src"))

from campaign import Campaign
from enemies import StatusEffect


def test_use_food_water_and_antidote():
    camp = Campaign([])
    inv = camp.inventory

    inv.add_item("food", 1)
    inv.add_item("water", 1)
    inv.add_item("antidote", 1)

    camp.status_effects = [
        StatusEffect("hunger", 2),
        StatusEffect("thirst", 2),
        StatusEffect("poison", 2),
    ]

    inv.use_item("food", camp)
    assert not inv.has_item("food")
    assert all(e.effect_type != "hunger" for e in camp.status_effects)

    inv.use_item("water", camp)
    assert not inv.has_item("water")
    assert all(e.effect_type != "thirst" for e in camp.status_effects)

    inv.use_item("antidote", camp)
    assert not inv.has_item("antidote")
    assert all(e.effect_type != "poison" for e in camp.status_effects)

