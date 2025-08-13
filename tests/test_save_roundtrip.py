from pathlib import Path
import pathlib
import sys

BASE = pathlib.Path(__file__).resolve().parents[1]
if str(BASE / "src") not in sys.path:
    sys.path.insert(0, str(BASE / "src"))
if str(BASE) not in sys.path:
    sys.path.insert(0, str(BASE))

from gamecore import board, rules, saveio, validate


def test_save_roundtrip(tmp_path: Path):
    rules.set_seed(99)
    state = board.create_game()
    for _ in range(3):
        direction = rules.RNG.choice(list(rules.DIRECTIONS.keys()))
        board.player_move(state, direction)
        board.end_turn(state)
    save_path = tmp_path / "game.json"
    validate.validate_state(state)
    saveio.save_game(state, save_path)
    seed_before = rules.RNG.get_state()["seed"]
    seq_after_save = [rules.RNG.next() for _ in range(3)]
    loaded = saveio.load_game(save_path)
    validate.validate_state(loaded)
    seq_after_load = [rules.RNG.next() for _ in range(3)]
    assert seq_after_save == seq_after_load
    assert [(p.x, p.y) for p in loaded.players] == [(p.x, p.y) for p in state.players]
    assert loaded.board.noise == state.board.noise
    assert loaded.turn == state.turn
    assert rules.RNG.get_state()["seed"] == seed_before
