from __future__ import annotations

import json
import uuid
import time
from pathlib import Path
from typing import Any, Dict

CONFIG_DIR = Path.home() / ".oko_zombie"
SAVE_DIR = CONFIG_DIR / "saves"
REPLAY_DIR = CONFIG_DIR / "replays"
SCREENSHOT_DIR = CONFIG_DIR / "screenshots"
CONFIG_FILE = CONFIG_DIR / "config.json"

DEFAULT_SAVE_CONFLICT_POLICY = "ask"

DEFAULT_CONFIG: Dict[str, Any] = {
    "volume": 1.0,  # legacy master volume
    "volume_master": 1.0,
    "volume_step": 1.0,
    "volume_hit": 1.0,
    "volume_ui": 1.0,
    "lang": "en",
    "window_size": [800, 600],
    "fullscreen": False,
    "bindings": {},
    "ui_scale": 1.0,
    "first_run": True,
    "config_version": 1,
    "master_url": "ws://localhost:8080",
    "record_replays": False,
    "telemetry_opt_in": False,
    "telemetry_endpoint": "",
    "telemetry_anonymous_id": "",
    "camera_follow_speed": 5.0,
    "camera_zoom_speed": 0.25,
    "camera_shake_scale": 1.0,
    "weather_enabled": True,
    "weather_intensity": 1.0,
    "fx_vignette": False,
    "fx_vignette_intensity": 0.5,
    "fx_desaturate": False,
    "fx_desaturate_intensity": 0.5,
    "fx_color": False,
    "fx_color_curve": [1.0, 1.0, 1.0],
    "fx_bloom": False,
    "fx_bloom_intensity": 0.5,
    "fps_cap": 60,
    "loader_batch_ms": 8,
    "perf_overlay": False,
    "last_invite": "",
    "default_lobby_privacy": "public",
    "reconnect_backoff": [1, 2, 5, 10],
    "auto_rejoin": True,
    "default_spectator": False,
    "save_conflict_policy": DEFAULT_SAVE_CONFLICT_POLICY,
}


def _ensure_dirs() -> None:
    SAVE_DIR.mkdir(parents=True, exist_ok=True)
    REPLAY_DIR.mkdir(parents=True, exist_ok=True)
    SCREENSHOT_DIR.mkdir(parents=True, exist_ok=True)


def load_config() -> Dict[str, Any]:
    """Load configuration from ``CONFIG_FILE``.

    Missing or invalid files return :data:`DEFAULT_CONFIG` and write it to disk.
    """

    _ensure_dirs()
    try:
        with CONFIG_FILE.open("r", encoding="utf-8") as fh:
            data = json.load(fh)
    except Exception:
        data = DEFAULT_CONFIG.copy()
        save_config(data)
    # merge in defaults for missing keys to keep backwards compatibility
    if "volume_master" not in data and "volume" in data:
        data["volume_master"] = data.get("volume", 1.0)
    for key, value in DEFAULT_CONFIG.items():
        data.setdefault(key, value)
    data["volume"] = data.get("volume_master", 1.0)
    if not data.get("telemetry_anonymous_id"):
        data["telemetry_anonymous_id"] = str(uuid.uuid4())
        save_config(data)
    return data


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


def replay_dir() -> Path:
    """Directory containing recorded replays."""

    _ensure_dirs()
    return REPLAY_DIR


def screenshot_dir() -> Path:
    """Directory containing captured screenshots."""

    _ensure_dirs()
    return SCREENSHOT_DIR


def screenshot_path(seed: int) -> Path:
    """Return a unique path for a screenshot.

    Filenames are composed of the current date/time and the supplied ``seed``
    to make runs with different seeds easier to identify.
    """

    timestamp = time.strftime("%Y%m%d_%H%M%S")
    return screenshot_dir() / f"{timestamp}_{seed}.png"
