"""Minimal JSON based i18n helper."""

from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Dict, TypeVar

DATA_DIR = Path(__file__).resolve().parents[2] / "data" / "locales"
DEFAULT_LANG = "en"

log = logging.getLogger(__name__)

_translations: Dict[str, str] = {}
_default: Dict[str, str] = {}
_missing: set[str] = set()


def _load(lang: str) -> Dict[str, str]:
    path = DATA_DIR / f"{lang}.json"
    with path.open("r", encoding="utf-8") as fh:
        return json.load(fh)


def set_language(lang: str) -> None:
    global _translations
    try:
        _translations = _load(lang)
    except FileNotFoundError:
        _translations = _default


try:  # load defaults at import time
    _default = _load(DEFAULT_LANG)
except FileNotFoundError:
    _default = {}
set_language(DEFAULT_LANG)


def gettext(key: str) -> str:
    return _translations.get(key, _default.get(key, key))


T = TypeVar("T")


def safe_get(key: str, default: T | None = None) -> T:
    if key in _translations:
        return _translations[key]  # type: ignore[return-value]
    if key in _default:
        return _default[key]  # type: ignore[return-value]
    if key not in _missing:
        log.warning("missing translation: %s", key)
        _missing.add(key)
    if default is not None:
        return default
    return key  # type: ignore[return-value]


__all__ = ["gettext", "set_language", "safe_get"]

