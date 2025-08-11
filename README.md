# Gamecore

## Installation

```bash
pip install -r requirements.txt
```

## CLI

```bash
python -m scripts.run_cli --seed 123
```

## GUI

```bash
python -m scripts.run_gui
```

## Tiles pipeline

Tile graphics are generated from `textures.json`. Run the helper script to
build individual 64×64 tiles and an atlas:

```bash
python tools/build_tiles.py
```

The client also checks `assets/tiles/` on startup and will automatically
invoke this script if the directory is empty, producing fallback tiles from
the JSON mapping.

## Localization

Text shown by both the CLI and the GUI is translated via a simple JSON based
system. Locale files live in `data/locales/<lang>.json` and the desired
language is stored in `~/.oko_zombie/config.json` under the `"lang"` key.
Missing keys default to the lookup key itself.

## Tests

```bash
pytest -q
```
