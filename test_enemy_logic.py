import random
import os
import sys

sys.path.append(os.path.join(os.path.dirname(__file__), "src"))

from enemies import Enemy, EnemyManager
from campaign import Campaign
from game_map import GameMap
from player import Player


def test_enemy_moves_faster_at_night_and_attacks():
    random.seed(0)
    gm = GameMap(5, 5, player_pos=(0, 0))
    player = Player(health=5, max_health=5)
    enemy = Enemy((3, 0), attack=2)
    manager = EnemyManager([enemy])
    camp = Campaign([], game_map=gm, player=player, enemies=manager)

    # day movement – one tile towards player
    manager.move_towards_player(gm.player_pos, gm.width, gm.height, camp)
    assert enemy.pos == (2, 0)

    # night movement – two tiles
    camp.time_of_day = "night"
    manager.move_towards_player(gm.player_pos, gm.width, gm.height, camp)
    assert enemy.pos == (0, 0)

    # enemy attacks and deals damage
    enemy.perform_attack(camp)
    assert camp.player.health == 3  # took 2 damage

