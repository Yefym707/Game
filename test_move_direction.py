import game


def make_game():
    return game.Game(
        board_size=10,
        num_players=1,
        num_ai=0,
        roles=["leader"],
        difficulty="easy",
        scenario=1,
        cooperative=False,
    )


def test_move_accepts_word_directions():
    g = make_game()
    player = g.player
    # Place the player away from edges and clear any walls for deterministic results
    player.x, player.y = 5, 5
    g.wall_positions = set()
    # Move north (up)
    assert g.move_player("north") is True
    assert (player.x, player.y) == (5, 4)
    # Move left (west)
    assert g.move_player("left") is True
    assert (player.x, player.y) == (4, 4)
    # Invalid direction should fail and not move the player
    assert g.move_player("upleft") is False
    assert (player.x, player.y) == (4, 4)
