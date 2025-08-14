import random
from src.player import Player
from src.game_board import GameBoard
from src.zombie import Zombie

def test_move_updates_board_and_actions():
    board = GameBoard(3, 3)
    player = Player(0, 0)
    board.place_entity(0, 0, player.symbol)
    player.start_turn(1)
    assert player.move(1, 0, board)
    assert (player.x, player.y) == (1, 0)
    assert board.grid[0][1] == player.symbol
    assert board.grid[0][0] is None
    assert player.actions_left == 0
    assert player.turn_over is True


def test_attack_adjacent_zombie():
    board = GameBoard(3, 3)
    player = Player(1, 1)
    zombie = Zombie(1, 2)
    board.place_entity(1, 1, player.symbol)
    board.place_entity(1, 2, 'Z')
    player.start_turn(1)
    assert player.attack(zombie)
    assert zombie.health == 2
    assert player.actions_left == 0
    assert player.turn_over is True


def test_search_picks_up_supply_token():
    board = GameBoard(3, 3)
    player = Player(1, 1)
    board.place_entity(1, 1, player.symbol)
    board.items = {(1, 1): 'supply'}
    player.start_turn(1)
    found = player.search(board)
    assert found == 'supply'
    assert player.inventory.has_item('supply')
    assert (1, 1) not in board.items
    assert player.actions_left == 0
    assert player.turn_over is True


def test_search_random_find(monkeypatch):
    board = GameBoard(3, 3)
    player = Player(0, 0)
    board.place_entity(0, 0, player.symbol)
    player.start_turn(1)
    # force random.random to always return 0 so search succeeds
    monkeypatch.setattr(random, 'random', lambda: 0.0)
    found = player.search(board)
    assert found == 'supply'
    assert player.inventory.has_item('supply')
    assert player.actions_left == 0
    assert player.turn_over is True
