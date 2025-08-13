"""Minimal JSON based internationalisation helper."""
from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Dict, TypeVar

from client.util_paths import resource_path

CONFIG_PATH = Path.home() / ".oko_zombie" / "config.json"
# Language code used as a fallback for missing keys/translations
DEFAULT_LANG = "en"


def _load_lang() -> str:
    try:
        with CONFIG_PATH.open("r", encoding="utf-8") as fh:
            data = json.load(fh)
            return data.get("lang", DEFAULT_LANG)
    except Exception:  # pragma: no cover - missing config
        return DEFAULT_LANG


def _load_translations(lang: str) -> Dict[str, str]:
    path = Path(resource_path(f"data/locales/{lang}.json"))
    try:
        with path.open("r", encoding="utf-8") as fh:
            return json.load(fh)
    except FileNotFoundError:
        if lang != DEFAULT_LANG:
            return _load_translations(DEFAULT_LANG)
        return {}


# Load default translations once so they are always available as a fallback
_default_translations: Dict[str, str] = _load_translations(DEFAULT_LANG)

# Load current language from the config and its translations
_LANG = _load_lang()
_translations: Dict[str, str] = _load_translations(_LANG)
_missing_logged: set[str] = set()


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

    # first try the active language, then fall back to default translations
    if key in _translations:
        return _translations[key]
    return _default_translations.get(key, key)


T = TypeVar("T")


def safe_get(key: str, default: T | None = None) -> T:
    """Return translation for ``key`` or a fallback.

    Missing keys are logged once per process.  When ``default`` is ``None`` the
    key itself is returned mirroring :func:`gettext` behaviour.
    """

    if key in _translations:
        return _translations[key]  # type: ignore[return-value]
    if key in _default_translations:
        return _default_translations[key]  # type: ignore[return-value]
    if key not in _missing_logged:
        logging.getLogger(__name__).warning("missing translation: %s", key)
        _missing_logged.add(key)
    if default is not None:
        return default
    return key  # type: ignore[return-value]


# common translation keys used by the client -------------------------------
PLAY = "PLAY"
CONTINUE = "CONTINUE"
SETTINGS = "SETTINGS"
SOLO = "SOLO"
LOCAL_COOP = "LOCAL_COOP"
ONLINE = "ONLINE"
BACK = "BACK"
NEW_GAME = "menu_new_game"
LOAD_GAME = "menu_load"
QUIT = "menu_quit"
MODE = "mode"
SEED = "seed"
RANDOM = "random"
NO_SAVE_FOUND = "no_save_found"
SLOT = "slot"
DELETE = "delete"
CONFIRM_DELETE = "confirm_delete"
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

ACHIEVEMENTS = "ACHIEVEMENTS"
CLOUD = "CLOUD"
OVERLAY = "OVERLAY"

# save conflict handling -----------------------------------------------------
SAVE_CONFLICT_POLICY = "save_conflict_policy"
PREFER_LOCAL = "prefer_local"
PREFER_CLOUD = "prefer_cloud"
ASK = "ask"
SAVE_CONFLICT_TITLE = "save_conflict_title"
LOCAL_VERSION = "local_version"
CLOUD_VERSION = "cloud_version"
ALWAYS_PREFER_LOCAL = "always_prefer_local"
ALWAYS_PREFER_CLOUD = "always_prefer_cloud"
OPEN_BACKUPS_FOLDER = "open_backups_folder"

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
HIGH_CONTRAST = "high_contrast"
SUBTITLES = "subtitles"
DYSLEXIA_FONT = "dyslexia_font"
ACCESSIBILITY = "accessibility"
INVERT_ZOOM = "invert_zoom"
LARGE_TEXT = "large_text"
NIGHT_VIGNETTE = "night_vignette"

# minimap legend -------------------------------------------------------------
LEGEND_WALL = "legend_wall"
LEGEND_FLOOR = "legend_floor"
LEGEND_LOOT = "legend_loot"
LEGEND_PLAYER = "legend_player"
LEGEND_ZOMBIE = "legend_zombie"
LEGEND_GOAL = "legend_goal"

# invite related --------------------------------------------------------------
INVITE = "INVITE"
COPY_LINK = "COPY_LINK"
COPY_CODE = "COPY_CODE"
JOIN_BY_CODE = "JOIN_BY_CODE"
INVITE_INVALID = "INVITE_INVALID"
INVITE_EXPIRED = "INVITE_EXPIRED"
COPIED = "COPIED"
NOT_READY = "NOT_READY"
PUBLIC = "PUBLIC"
PRIVATE = "PRIVATE"
PING_MS = "PING_MS"
RECONNECTING = "RECONNECTING"
INVITE_REVOKED = "INVITE_REVOKED"
INVITE_UPDATED = "INVITE_UPDATED"
REJOIN = "REJOIN"
SPECTATE = "SPECTATE"
VOTE_PAUSE = "VOTE_PAUSE"
VOTE_RESUME = "VOTE_RESUME"
DROP_IN = "DROP_IN"
PAUSED_BY_VOTE = "PAUSED_BY_VOTE"
