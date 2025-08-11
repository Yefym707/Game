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


def test_create_noise_accepts_word_directions():
    g = make_game()
    player = g.player
    # ensure known position away from edges
    player.x = 5
    player.y = 5
    player.supplies = 1
    g.noise_markers = []
    result = g.create_noise(direction="north")
    assert result is True
    assert player.supplies == 0
    assert g.noise_markers[0][:2] == (5, 4)


def test_create_noise_invalid_direction():
    g = make_game()
    player = g.player
    player.supplies = 1
    g.noise_markers = []
    assert g.create_noise(direction="upleft") is False
    assert g.noise_markers == []
    assert player.supplies == 1


def test_create_noise_prevents_out_of_bounds():
    g = make_game()
    player = g.player
    player.supplies = 1
    player.y = 0  # top edge
    g.noise_markers = []
    assert g.create_noise(direction="north") is False
    assert g.noise_markers == []
    assert player.supplies == 1
