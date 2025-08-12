from pathlib import Path

from src.gamecore import board, rules, saveio


def test_save_roundtrip(tmp_path: Path):
    rules.set_seed(99)
    state = board.create_game()
    for _ in range(3):
        direction = rules.RNG.choice(list(rules.DIRECTIONS.keys()))
        board.player_move(state, direction)
        board.end_turn(state)
    save_path = tmp_path / "game.json"
    saveio.save_game(state, save_path)
    seq_after_save = [rules.RNG.next() for _ in range(3)]
    loaded = saveio.load_game(save_path)
    seq_after_load = [rules.RNG.next() for _ in range(3)]
    assert seq_after_save == seq_after_load
    assert [(p.x, p.y) for p in loaded.players] == [(p.x, p.y) for p in state.players]
    assert loaded.board.noise == state.board.noise
