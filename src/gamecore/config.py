"""Lightweight configuration storage."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict

CONFIG_DIR = Path.home() / ".oko_zombie"
CONFIG_FILE = CONFIG_DIR / "config.json"

DEFAULT_CONFIG: Dict[str, Any] = {
    "last_used_slot": None,
    "default_player_names": ["Alice", "Bob", "Carol", "Dave"],
    "last_seed": 0,
    "ui_scale": 1.0,
    "fx_preset": "HIGH",
    "audio_enabled": True,
    "disable_online": False,
    "ui_theme": "dark",
    "language": "en",
}


def load_config() -> Dict[str, Any]:
    CONFIG_DIR.mkdir(parents=True, exist_ok=True)
    try:
        with CONFIG_FILE.open("r", encoding="utf-8") as fh:
            data = json.load(fh)
    except Exception:
        data = {}
    cfg = DEFAULT_CONFIG.copy()
    cfg.update(data)
    return cfg


def save_config(cfg: Dict[str, Any]) -> None:
    CONFIG_DIR.mkdir(parents=True, exist_ok=True)
    with CONFIG_FILE.open("w", encoding="utf-8") as fh:
        json.dump(cfg, fh, indent=2)


__all__ = ["load_config", "save_config", "CONFIG_DIR"]

