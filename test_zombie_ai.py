import os
import sys

sys.path.append(os.path.join(os.path.dirname(__file__), "src"))

from zombie import Zombie
from player import Player


def test_zombie_moves_toward_nearest_player():
    board = [[0 for _ in range(5)] for _ in range(5)]
    players = [Player(x=0, y=0), Player(x=4, y=4)]
    zombie = Zombie(x=2, y=0)
    zombie.take_turn(players, board)
    assert zombie.get_position() == (1, 0)


def test_zombie_attacks_adjacent_player():
    board = [[0 for _ in range(3)] for _ in range(3)]
    player = Player(x=1, y=1, health=5)
    zombie = Zombie(x=1, y=0)
    zombie.take_turn([player], board)
    assert zombie.get_position() == (1, 0)
    assert player.get_health() == 4
