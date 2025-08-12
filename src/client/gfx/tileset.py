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

    def draw(
        self,
        surface: pygame.Surface,
        key: str,
        pos: tuple[int, int],
        scale: float = 1.0,
    ) -> None:
        """Draw ``key`` tile at ``pos`` with optional ``scale``.

        Scaling uses nearest-neighbour filtering via ``pygame.transform.scale``
        which keeps the pixel art crisp even when enlarged.
        """

        tile = self.get(key)
        if not tile:
            return
        if scale != 1.0:
            size = int(TILE_SIZE * scale)
            img = pygame.transform.scale(tile, (size, size))
        else:
            img = tile
        surface.blit(img, pos)


_icon_cache: Dict[tuple[str, int, tuple[int, int, int]], pygame.Surface] = {}


def render_icon(char: str, size: int, color: tuple[int, int, int] = (255, 255, 255)) -> pygame.Surface:
    """Return a ``Surface`` containing ``char`` rendered via ``pygame.font``.

    The result is cached based on the character, size and color so repeated
    calls are inexpensive.  This helper avoids shipping any binary assets for
    simple UI icons.
    """

    key = (char, size, color)
    surf = _icon_cache.get(key)
    if surf is None:
        font = pygame.font.SysFont(None, size)
        surf = font.render(char, True, color)
        _icon_cache[key] = surf
    return surf
