"""Minimal localisation helper with fallback to English.

Loads string tables from ``data/locales`` and exposes :func:`gettext` (also
available as :func:`tr`).  English strings are always loaded so missing keys in
other languages fall back gracefully.
"""

from __future__ import annotations

import json
import os
from typing import Dict

_DEFAULT_LANG = "en"
_LOCALES_DIR = os.path.join(os.path.dirname(__file__), "..", "..", "data", "locales")

_current_lang = _DEFAULT_LANG
_default_strings: Dict[str, str] = {}
_strings: Dict[str, str] = {}


def _load_locale(lang: str) -> Dict[str, str]:
    path = os.path.join(_LOCALES_DIR, f"{lang}.json")
    try:
        with open(path, "r", encoding="utf-8") as fh:
            return json.load(fh)
    except FileNotFoundError:
        return {}


def set_language(lang: str) -> None:
    """Select active language and load translations."""
    global _current_lang, _strings
    _current_lang = lang
    _strings = dict(_default_strings)
    if lang != _DEFAULT_LANG:
        _strings.update(_load_locale(lang))


def gettext(key: str) -> str:
    """Return translated text for ``key``."""
    return _strings.get(key, _default_strings.get(key, key))


# Short alias used throughout the code base
tr = gettext

# Load default strings on import
_default_strings = _load_locale(_DEFAULT_LANG)
_strings = dict(_default_strings)

# Commonly referenced key constant used in tests
PLAY = "play"
