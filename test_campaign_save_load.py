import os
import sys

sys.path.append(os.path.join(os.path.dirname(__file__), "src"))

from campaign import Campaign
from enemies import EnemyManager, Enemy
from game_map import GameMap
from inventory import Inventory
from player import Player


def test_campaign_can_be_saved_and_loaded(tmp_path):
    gm = GameMap(4, 4, player_pos=(1, 1))
    inv = Inventory({"food": 2}, coins=5)
    player = Player(health=4, max_health=5)
    enemies = EnemyManager([Enemy((2, 2))])

    camp = Campaign(
        [],
        game_map=gm,
        inventory=inv,
        player=player,
        enemies=enemies,
        turn_count=3,
        time_of_day="night",
    )

    path = tmp_path / "save.json"
    camp.save(path)

    loaded = Campaign.load(path, [])

    assert loaded.game_map.player_pos == (1, 1)
    assert loaded.inventory.coins == 5
    assert loaded.player.health == 4
    assert loaded.time_of_day == "night"
    assert loaded.turn_count == 3

