import sys
import pathlib

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "src"))

from gamecore import board, rules


def test_bounds_and_corner_clipping() -> None:
    rules.set_seed(0)
    state = board.create_game(width=2, height=2, players=1, zombies=0)
    # Player starts at (0,0)
    assert not board.player_move(state, "a")  # left out of bounds
    assert not board.player_move(state, "w")  # up out of bounds
    # Block adjacent tiles to test corner clipping
    state.board.tiles[0][1] = "#"
    state.board.tiles[1][0] = "#"
    assert not board.player_move(state, "c")  # moving to (1,1) diagonally
