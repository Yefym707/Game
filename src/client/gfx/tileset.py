"""Tileset loader and fallback generator."""
from __future__ import annotations

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
        """Generate PNG tiles via :mod:`tools.build_tiles`.

        The helper searches for ``textures.json`` either in the project root or
        next to the ``scripts`` package and invokes :func:`tools.build_tiles.generate`
        to render the tiles using Pillow.
        """

        from tools import build_tiles

        mapping_path: Path | None = None
        for loc in (root / "textures.json", root / "scripts" / "textures.json"):
            if loc.exists():
                mapping_path = loc
                break
        if mapping_path and mapping_path.exists():
            build_tiles.generate(mapping_path)
        else:  # minimal fallback to player glyph
            tiles = build_tiles.build_tiles({"@": "@"})
            build_tiles.build_atlas(tiles)

    # public -----------------------------------------------------------
    def get(self, key: str) -> pygame.Surface | None:
        return self.tiles.get(key)
