import json
import game


def test_load_textures_merges_with_defaults(tmp_path):
    file = tmp_path / "tex.json"
    file.write_text('{"Z": "x"}')
    textures = game.load_textures(str(file))
    # custom value overrides default
    assert textures["Z"] == "x"
    # unspecified values fall back to default
    assert textures[game.WALL_SYMBOL] == game.WALL_SYMBOL


def test_load_textures_missing_file_returns_copy(tmp_path):
    missing = tmp_path / "missing.json"
    textures = game.load_textures(str(missing))
    textures["."] = "X"
    # default textures remain unchanged
    assert game.DEFAULT_TEXTURES["."] == "."


def test_game_accepts_custom_texture_file(tmp_path):
    file = tmp_path / "tex.json"
    file.write_text(json.dumps({"Z": "!"}))
    g = game.Game(
        board_size=10,
        num_players=1,
        num_ai=0,
        roles=["leader"],
        difficulty="easy",
        scenario=1,
        cooperative=False,
        texture_file=str(file),
    )
    assert g.textures["Z"] == "!"
    # Ensure unspecified entries still exist
    assert g.textures[game.WALL_SYMBOL] == game.WALL_SYMBOL
