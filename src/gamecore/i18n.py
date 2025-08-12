"""Minimal JSON based internationalisation helper."""
from __future__ import annotations

import json
from pathlib import Path
from typing import Dict

CONFIG_PATH = Path.home() / ".oko_zombie" / "config.json"
LOCALES_DIR = Path(__file__).resolve().parents[2] / "data" / "locales"
DEFAULT_LANG = "en"


def _load_lang() -> str:
    try:
        with CONFIG_PATH.open("r", encoding="utf-8") as fh:
            data = json.load(fh)
            return data.get("lang", DEFAULT_LANG)
    except Exception:  # pragma: no cover - missing config
        return DEFAULT_LANG


def _load_translations(lang: str) -> Dict[str, str]:
    try:
        with (LOCALES_DIR / f"{lang}.json").open("r", encoding="utf-8") as fh:
            return json.load(fh)
    except FileNotFoundError:  # pragma: no cover - missing locale
        return {}


_LANG = _load_lang()
_translations: Dict[str, str] = _load_translations(_LANG)


def set_language(lang: str) -> None:
    """Reload translations for ``lang`` and remember it globally."""

    global _LANG, _translations
    _LANG = lang
    _translations = _load_translations(lang)


def gettext(key: str) -> str:
    """Return a translated string for ``key``.

    Unknown keys fall back to ``key`` itself allowing the code to run even if
    a translation is missing.
    """

    return _translations.get(key, key)


# common translation keys used by the client -------------------------------
PLAY = "PLAY"
CONTINUE = "CONTINUE"
SETTINGS = "SETTINGS"
SOLO = "SOLO"
LOCAL_COOP = "LOCAL_COOP"
ONLINE = "ONLINE"
BACK = "BACK"
CONNECT = "CONNECT"
ADDRESS = "ADDRESS"
LOBBY = "LOBBY"
READY = "READY"
START = "START"
PING = "PING"
DISCONNECTED = "DISCONNECTED"
BROWSE = "BROWSE"
REFRESH = "REFRESH"
REPLAYS = "REPLAYS"
PLAY_REPLAY = "PLAY_REPLAY"
PAUSE = "PAUSE"
STEP = "STEP"
SPEED = "SPEED"
GOTO_TURN = "GOTO_TURN"
TELEMETRY_OPT_IN = "telemetry_opt_in"
TELEMETRY_ENDPOINT = "telemetry_endpoint"
SEND_TEST_EVENT = "send_test_event"
TELEMETRY_STATUS_SENT = "telemetry_status_sent"
TELEMETRY_STATUS_QUEUED = "telemetry_status_queued"
TELEMETRY_STATUS_ERROR = "telemetry_status_error"

# audio settings --------------------------------------------------------------
MASTER_VOLUME = "master_volume"
STEP_VOLUME = "step_volume"
HIT_VOLUME = "hit_volume"
UI_VOLUME = "ui_volume"

# additional UI keys
RESUME = "resume"
RESTART = "restart"
EASY = "easy"
NORMAL = "normal"
HARD = "hard"
TOOLTIP_MOVE = "tooltip_move"
TOOLTIP_ATTACK = "tooltip_attack"
LOG_EXPAND = "log_expand"
LOG_COLLAPSE = "log_collapse"

# events and scenarios -------------------------------------------------------
EVENT_ACCEPT = "event_accept"
EVENT_IGNORE = "event_ignore"
EVENT_OK = "event_ok"
SCENARIO_SHORT_NAME = "scenario_short_name"
SCENARIO_MEDIUM_NAME = "scenario_medium_name"
SCENARIO_LONG_NAME = "scenario_long_name"

# time of day ---------------------------------------------------------------
DAY = "time_day"
DUSK = "time_dusk"
NIGHT = "time_night"
DAWN = "time_dawn"

# ui theme & minimap --------------------------------------------------------
THEME_LIGHT = "theme_light"
THEME_DARK = "theme_dark"
THEME_APOCALYPSE = "theme_apocalypse"
UI_THEME = "ui_theme"
SHOW_MINIMAP = "show_minimap"
MINIMAP_SIZE = "minimap_size"
