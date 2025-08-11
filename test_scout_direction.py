import builtins
from unittest.mock import patch

import game


def test_scout_direction_reveals_correct_tile():
    g = game.Game(board_size=10, num_players=1, num_ai=0, roles=["leader"], difficulty="easy", scenario=1, cooperative=False)
    player = g.player
    g.revealed = {(player.x, player.y)}
    with patch.object(game, "SCOUT_RADIUS", 0):
        with patch("builtins.input", return_value="w"):
            g.scout()
    expected = (player.x, player.y - 1)
    assert expected in g.revealed
    assert (player.x - 1, player.y) not in g.revealed
