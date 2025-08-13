import json
from pathlib import Path


def _flatten(data, prefix=""):
    keys = set()
    for key, value in data.items():
        name = f"{prefix}{key}"
        if isinstance(value, dict):
            keys |= _flatten(value, name + ".")
        else:
            keys.add(name)
    return keys


def test_locales_sync():
    base = Path("data/locales")
    with (base / "en.json").open(encoding="utf-8") as fh:
        en = json.load(fh)
    with (base / "ru.json").open(encoding="utf-8") as fh:
        ru = json.load(fh)
    assert _flatten(en) == _flatten(ru)
