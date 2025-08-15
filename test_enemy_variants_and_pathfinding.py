import random
import os
import sys

sys.path.append(os.path.join(os.path.dirname(__file__), "src"))

from src.enemies import Enemy, EnemyManager, FastZombie, BruteZombie
from src.game_map import GameMap
from src.campaign import Campaign
from src.player import Player


def test_pathfinding_avoids_walls():
    gm = GameMap(5, 5, player_pos=(2, 0))
    player = Player()
    enemy = Enemy((0, 0))
    manager = EnemyManager([enemy])
    camp = Campaign([], game_map=gm, player=player, enemies=manager)
    camp.board_layout = [
        ".#...",
        ".....",
        ".....",
        ".....",
        ".....",
    ]
    manager.move_towards_player(gm.player_pos, gm.width, gm.height, camp)
    assert enemy.pos == (0, 1)


def test_enemy_variants_behaviour(monkeypatch):
    gm = GameMap(5, 5, player_pos=(2, 2), zones=[])
    player = Player(health=10, max_health=10)
    fz = FastZombie((0, 0))
    bz = BruteZombie((4, 4))
    manager = EnemyManager([fz, bz])
    camp = Campaign([], game_map=gm, player=player, enemies=manager)
    camp.board_layout = ["....." for _ in range(5)]
    # movement
    manager.move_towards_player(gm.player_pos, gm.width, gm.height, camp)
    assert fz.pos == (2, 0)
    assert bz.pos in {(3, 4), (4, 3)}
    manager.move_towards_player(gm.player_pos, gm.width, gm.height, camp)
    assert bz.pos in {(3, 4), (4, 3)}  # brute skips second move
    # attacks
    monkeypatch.setattr(random, 'random', lambda: 0.0)
    fz.perform_attack(camp)
    assert player.health == 8  # two hits of 1 damage
    bz.perform_attack(camp)
    assert player.health == 6  # brute deals 2 damage
