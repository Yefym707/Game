from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict

CONFIG_DIR = Path.home() / ".oko_zombie"
SAVE_DIR = CONFIG_DIR / "saves"
CONFIG_FILE = CONFIG_DIR / "config.json"

DEFAULT_CONFIG: Dict[str, Any] = {
    "volume": 1.0,
    "lang": "en",
    "window_size": [800, 600],
    "fullscreen": False,
}


def _ensure_dirs() -> None:
    SAVE_DIR.mkdir(parents=True, exist_ok=True)


def load_config() -> Dict[str, Any]:
    """Load configuration from ``CONFIG_FILE``.

    Missing or invalid files return :data:`DEFAULT_CONFIG` and write it to disk.
    """

    _ensure_dirs()
    try:
        with CONFIG_FILE.open("r", encoding="utf-8") as fh:
            return json.load(fh)
    except Exception:
        save_config(DEFAULT_CONFIG)
        return DEFAULT_CONFIG.copy()


def save_config(cfg: Dict[str, Any]) -> None:
    """Persist ``cfg`` to ``CONFIG_FILE``."""

    _ensure_dirs()
    with CONFIG_FILE.open("w", encoding="utf-8") as fh:
        json.dump(cfg, fh, indent=2)


def quicksave_path() -> Path:
    """Return path for the quick save file."""

    return SAVE_DIR / "quick.json"


def autosave_path() -> Path:
    """Return path for the auto save file."""

    return SAVE_DIR / "autosave.json"
