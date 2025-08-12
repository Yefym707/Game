import json
from pathlib import Path

from gamecore import board, rules, saveio


def create_v1_save(path: Path) -> None:
    """Create a fake version 1 save file at ``path``."""
    rules.set_seed(42)
    state = board.create_game(width=4, height=4, zombies=0, players=1)
    data = {
        "save_version": 1,
        "player": state.players[0].to_dict(),
        "state": state.to_dict(),
    }
    with path.open("w", encoding="utf-8") as fh:
        json.dump(data, fh)
    return state


def test_migrate_v1_to_current(tmp_path: Path) -> None:
    save_path = tmp_path / "v1_save.json"
    original_state = create_v1_save(save_path)

    loaded_state = saveio.load_game(save_path)

    assert loaded_state.mode is rules.GameMode.SOLO
    assert len(loaded_state.players) == 1
    assert loaded_state.players[0].to_dict() == original_state.players[0].to_dict()
    assert loaded_state.board.to_dict() == original_state.board.to_dict()
    assert loaded_state.turn == original_state.turn
