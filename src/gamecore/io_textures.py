from __future__ import annotations

import json
import os
from typing import Dict

DEFAULT_TEXTURES: Dict[str, str] = {
    ".": ".",
    "@": "@",
    "Z": "Z",
}


def load_textures(path: str | None = None) -> Dict[str, str]:
    if path is None:
        path = "textures.json"
    if os.path.exists(path):
        with open(path, "r", encoding="utf-8") as fh:
            return json.load(fh)
    return DEFAULT_TEXTURES
