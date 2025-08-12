from src.gamecore import board, rules


def test_bounds_and_corner_clipping():
    rules.set_seed(0)
    state = board.create_game(width=3, height=3, zombies=0)
    # out of bounds moves
    assert not board.player_move(state, 'a')
    assert not board.player_move(state, 'w')
    # place blocking tiles around target diagonal
    state.board.tiles[0][1] = '#'
    state.board.tiles[1][0] = '#'
    assert not board.player_move(state, 'c')
    # clear walls allows diagonal move
    state.board.tiles[0][1] = '.'
    state.board.tiles[1][0] = '.'
    assert board.player_move(state, 'c')
