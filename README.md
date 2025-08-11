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

Place `textures.json` either next to `scripts/run_gui.py` or in the project root.
If `assets/tiles/*.png` are missing the first launch will generate them
from the mapping in `textures.json`.

## Tests

```bash
pytest -q
```
