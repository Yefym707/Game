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
