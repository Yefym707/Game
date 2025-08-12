import json
from pathlib import Path
import sys
import pathlib

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "src"))

from gamecore import board, saveio, validate


def test_migrate_v1_to_v2(tmp_path: Path) -> None:
    state = board.create_game(zombies=0)
    old_save = {
        "save_version": 1,
        "player": state.players[0].to_dict(),
        "state": state.to_dict(),
    }
    path = tmp_path / "old.json"
    path.write_text(json.dumps(old_save))
    loaded = saveio.load_game(path)
    # Should now have a players list
    assert len(loaded.players) == 1
    validate.validate_state(loaded)
