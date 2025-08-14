import os
import sys


sys.path.append(os.path.join(os.path.dirname(__file__), "src"))

from campaign import Campaign
from enemies import StatusEffect


def test_use_food_water_and_antidote():
    camp = Campaign([])
    inv = camp.inventory

    inv.add_item("еда", 1)
    inv.add_item("вода", 1)
    inv.add_item("противоядие", 1)

    camp.status_effects = [
        StatusEffect("hunger", 2),
        StatusEffect("thirst", 2),
        StatusEffect("poison", 2),
    ]

    inv.use_item("еда", camp)
    assert not inv.has_item("еда")
    assert all(e.effect_type != "hunger" for e in camp.status_effects)

    inv.use_item("вода", camp)
    assert not inv.has_item("вода")
    assert all(e.effect_type != "thirst" for e in camp.status_effects)

    inv.use_item("противоядие", camp)
    assert not inv.has_item("противоядие")
    assert all(e.effect_type != "poison" for e in camp.status_effects)

