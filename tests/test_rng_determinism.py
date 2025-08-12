from src.gamecore import board, rules


def run(seed: int):
    rules.set_seed(seed)
    state = board.create_game()
    history = []
    for _ in range(5):
        direction = rules.RNG.choice(list(rules.DIRECTIONS.keys()))
        moved = board.player_move(state, direction)
        board.end_turn(state)
        history.append((direction, moved, [(p.x, p.y) for p in state.players], [(z.x, z.y) for z in state.zombies]))
    return history


def test_rng_determinism():
    h1 = run(123)
    h2 = run(123)
    assert h1 == h2
