import pytest
from src.game_board import GameBoard


def test_default_size_and_free_tiles():
    board = GameBoard()
    assert board.width == 10 and board.height == 10
    # all tiles should be free at start
    for x in range(board.width):
        for y in range(board.height):
            assert board.is_tile_free(x, y)


def test_place_and_remove_entity():
    board = GameBoard(5, 5)
    board.place_entity(1, 1, 'P')
    assert not board.is_tile_free(1, 1)
    board.remove_entity(1, 1)
    assert board.is_tile_free(1, 1)


def test_bounds_and_errors():
    board = GameBoard(3, 3)
    with pytest.raises(ValueError):
        board.place_entity(3, 0, 'P')
    with pytest.raises(ValueError):
        board.remove_entity(-1, 0)
    assert not board.within_bounds(3, 3)
    assert board.is_tile_free(3, 3) is False


def test_display_board():
    board = GameBoard(3, 2)
    board.place_entity(0, 0, 'P')
    board.place_entity(1, 0, 'Z')
    expected = "PZ.\n..."
    assert board.display_board() == expected
