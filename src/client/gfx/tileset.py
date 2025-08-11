"""Tileset loader and fallback generator."""
from __future__ import annotations

import json
from pathlib import Path
from typing import Dict

import pygame

TILE_SIZE = 64


class Tileset:
    """Load PNG tiles or generate them from ``textures.json``."""

    def __init__(self, folder: Path | None = None) -> None:
        root = Path(__file__).resolve().parents[3]
        self.folder = folder or root / "assets" / "tiles"
        self.folder.mkdir(parents=True, exist_ok=True)
        pygame.font.init()
        self.tiles: Dict[str, pygame.Surface] = {}
        self._load(root)

    # internal ---------------------------------------------------------
    def _load(self, root: Path) -> None:
        pngs = list(self.folder.glob("*.png"))
        if not pngs:
            self._generate_from_json(root)
            pngs = list(self.folder.glob("*.png"))
        for path in pngs:
            self.tiles[path.stem] = pygame.image.load(path.as_posix()).convert_alpha()

    def _generate_from_json(self, root: Path) -> None:
        mapping: Dict[str, str] = {}
        for loc in (root / "textures.json", root / "scripts" / "textures.json"):
            if loc.exists():
                with open(loc, "r", encoding="utf8") as fh:
                    mapping = json.load(fh)
                break
        mapping.setdefault("@", "@")
        font = pygame.font.SysFont(None, 48)
        for key, glyph in mapping.items():
            surf = pygame.Surface((TILE_SIZE, TILE_SIZE), pygame.SRCALPHA)
            img = font.render(glyph, True, (255, 255, 255))
            rect = img.get_rect(center=(TILE_SIZE // 2, TILE_SIZE // 2))
            surf.blit(img, rect)
            pygame.image.save(surf, self.folder / f"{key}.png")
            self.tiles[key] = surf

    # public -----------------------------------------------------------
    def get(self, key: str) -> pygame.Surface | None:
        return self.tiles.get(key)
