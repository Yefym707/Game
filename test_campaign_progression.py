import os
import sys

sys.path.append(os.path.join(os.path.dirname(__file__), "src"))

from campaign import Campaign
from scenario import Scenario
from game_map import GameMap
from inventory import Inventory
from player import Player
from enemies import EnemyManager, Enemy


def test_campaign_advances_scenarios_and_carries_legacy():
    gm = GameMap(4, 4, player_pos=(0, 0))
    inv = Inventory()
    player = Player(health=4, max_health=5)
    enemies = EnemyManager([Enemy((1, 1))])
    scenarios = [
        Scenario("S1", "First", {}),
        Scenario("S2", "Second", {}),
    ]
    camp = Campaign(scenarios, game_map=gm, inventory=inv, player=player, enemies=enemies)

    first = camp.start_next_scenario()
    assert first.name == "S1"
    # award bonus for winning first scenario
    camp.record_scenario_result("player", legacy_bonus={"bonus_health": 1, "items": {"medal": 1}})

    second = camp.start_next_scenario()
    assert second.name == "S2"
    # legacy effects applied
    assert camp.player.max_health == 6
    assert camp.player.health == 5  # healed when bonus applied
    assert camp.inventory.has_item("medal")

    # finishing the last scenario ends the campaign
    camp.record_scenario_result("player")
    assert camp.start_next_scenario() is None
    assert camp.progress["campaign_complete"]
