from pathlib import Path
import sys
import pathlib

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "src"))

from gamecore import board, rules, saveio


def test_rng_determinism(tmp_path: Path) -> None:
    """Saving and loading must preserve RNG state."""
    rules.set_seed(123)
    state = board.create_game(zombies=0)
    # Advance RNG and save the state afterwards.
    first = rules.RNG.randrange(1000)
    save_path = tmp_path / "save.json"
    saveio.save_game(state, save_path)
    # Generate another value so the stream moves forward.
    second = rules.RNG.randrange(1000)
    # Reloading the save should restore the RNG to the point right after
    # ``first`` was generated, making the next value equal to ``second``.
    saveio.load_game(save_path)
    assert rules.RNG.randrange(1000) == second
