"""Lightweight configuration storage."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict

CONFIG_DIR = Path.home() / ".oko_zombie"
CONFIG_FILE = CONFIG_DIR / "config.json"

DEFAULT_SAVE_CONFLICT_POLICY = "ask"
SAVE_CONFLICT_POLICIES = ("ask", "prefer_local", "prefer_cloud")

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
    "keybinds": {},
    "save_conflict_policy": DEFAULT_SAVE_CONFLICT_POLICY,
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
    val = cfg.get("save_conflict_policy")
    cfg["save_conflict_policy"] = normalize_save_conflict_policy(val if isinstance(val, str) else DEFAULT_SAVE_CONFLICT_POLICY)
    try:
        from client.input_map import InputManager

        if not isinstance(cfg.get("keybinds"), dict):
            cfg["keybinds"] = InputManager.default_keybinds()
        else:
            cfg["keybinds"] = InputManager.from_config(cfg.get("keybinds")).to_config()
    except Exception:  # pragma: no cover - defensive
        pass
    return cfg


def save_config(cfg: Dict[str, Any]) -> None:
    CONFIG_DIR.mkdir(parents=True, exist_ok=True)
    with CONFIG_FILE.open("w", encoding="utf-8") as fh:
        json.dump(cfg, fh, indent=2)


def normalize_save_conflict_policy(val: str) -> str:
    return val if val in SAVE_CONFLICT_POLICIES else DEFAULT_SAVE_CONFLICT_POLICY


__all__ = [
    "load_config",
    "save_config",
    "CONFIG_DIR",
    "DEFAULT_SAVE_CONFLICT_POLICY",
    "SAVE_CONFLICT_POLICIES",
    "normalize_save_conflict_policy",
]

