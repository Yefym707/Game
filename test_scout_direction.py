from unittest.mock import patch

import game


def test_scout_direction_reveals_correct_tile():
    g = game.Game(
        board_size=10,
        num_players=1,
        num_ai=0,
        roles=["leader"],
        difficulty="easy",
        scenario=1,
        cooperative=False,
    )
    player = g.player
    g.revealed = {(player.x, player.y)}
    with patch.object(game, "SCOUT_RADIUS", 0):
        g.scout(direction="w")
    expected = (player.x, player.y - 1)
    assert expected in g.revealed
    assert (player.x - 1, player.y) not in g.revealed


def test_scout_blocked_by_wall():
    """Scouting should not reveal tiles hidden behind walls."""
    g = game.Game(
        board_size=10,
        num_players=1,
        num_ai=0,
        roles=["leader"],
        difficulty="easy",
        scenario=1,
        cooperative=False,
    )
    player = g.player
    # Move the player away from the edge to avoid out of bounds
    player.x, player.y = 2, 2
    g.revealed = {(player.x, player.y)}
    # Place a wall directly east of the player
    g.wall_positions = {(player.x + 1, player.y)}
    with patch.object(game, "SCOUT_RADIUS", 2):
        g.scout(direction="d")
    # The wall tile is revealed but the tile behind remains hidden
    assert (player.x + 1, player.y) in g.revealed
    assert (player.x + 2, player.y) not in g.revealed


def test_scout_accepts_word_directions():
    """Scouting should accept word-based directions such as 'up' or 'north'."""
    g = game.Game(
        board_size=10,
        num_players=1,
        num_ai=0,
        roles=["leader"],
        difficulty="easy",
        scenario=1,
        cooperative=False,
    )
    player = g.player
    g.revealed = {(player.x, player.y)}
    with patch.object(game, "SCOUT_RADIUS", 0):
        g.scout(direction="up")
    assert (player.x, player.y - 1) in g.revealed


def test_scout_prevents_out_of_bounds_reveal():
    g = game.Game(
        board_size=10,
        num_players=1,
        num_ai=0,
        roles=["leader"],
        difficulty="easy",
        scenario=1,
        cooperative=False,
    )
    player = g.player
    # Place the player on the top edge so scouting north would go out of bounds
    player.y = 0
    g.revealed = {(player.x, player.y)}
    with patch.object(game, "SCOUT_RADIUS", 0):
        result = g.scout(direction="w")
    assert result is False
    assert g.revealed == {(player.x, player.y)}
