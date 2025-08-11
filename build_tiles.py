#!/usr/bin/env python3
import json
import math
import sys
from pathlib import Path
from urllib.parse import quote

from PIL import Image, ImageDraw, ImageFont

TILE_SIZE = 64
ASSET_DIR = Path("assets")
TILES_DIR = ASSET_DIR / "tiles"


def escape_symbol(sym: str) -> str:
    encoded = quote(sym, safe="")
    return encoded.replace(".", "%2E")


def load_textures(path: Path) -> dict:
    with path.open(encoding="utf-8") as f:
        return json.load(f)


def load_font(size: int = 48) -> ImageFont.FreeTypeFont:
    try:
        return ImageFont.truetype("DejaVuSansMono.ttf", size=size)
    except Exception:
        return ImageFont.load_default()


def render_tile(texture: str, font: ImageFont.ImageFont) -> Image.Image:
    img = Image.new("RGBA", (TILE_SIZE, TILE_SIZE), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    bbox = draw.textbbox((0, 0), texture, font=font)
    w = bbox[2] - bbox[0]
    h = bbox[3] - bbox[1]
    x = (TILE_SIZE - w) // 2 - bbox[0]
    y = (TILE_SIZE - h) // 2 - bbox[1]
    draw.text((x, y), texture, font=font, fill=(0, 0, 0, 255))
    return img


def build_tiles(textures: dict) -> dict:
    TILES_DIR.mkdir(parents=True, exist_ok=True)
    font = load_font()
    tiles = {}
    for sym, tex in textures.items():
        img = render_tile(tex, font)
        filename = escape_symbol(sym) + ".png"
        img.save(TILES_DIR / filename)
        tiles[sym] = img
    return tiles


def build_atlas(tiles: dict) -> dict:
    symbols = list(tiles.keys())
    count = len(symbols)
    cols = math.ceil(math.sqrt(count))
    rows = math.ceil(count / cols)
    atlas = Image.new("RGBA", (cols * TILE_SIZE, rows * TILE_SIZE), (0, 0, 0, 0))
    mapping = {}
    for idx, sym in enumerate(symbols):
        row = idx // cols
        col = idx % cols
        x = col * TILE_SIZE
        y = row * TILE_SIZE
        atlas.paste(tiles[sym], (x, y))
        mapping[sym] = {"x": x, "y": y, "w": TILE_SIZE, "h": TILE_SIZE}
    atlas_path = ASSET_DIR / "tileset.png"
    atlas.save(atlas_path)
    mapping_path = ASSET_DIR / "tileset.json"
    with mapping_path.open("w", encoding="utf-8") as f:
        json.dump({"map": mapping}, f, ensure_ascii=False, indent=2)
    return mapping


def main() -> None:
    texture_file = Path(sys.argv[1]) if len(sys.argv) > 1 else Path("textures.json")
    textures = load_textures(texture_file)
    tiles = build_tiles(textures)
    build_atlas(tiles)
    print(f"Generated {len(tiles)} tiles in {TILES_DIR}")
    print("Atlas written to", ASSET_DIR / "tileset.png")


if __name__ == "__main__":
    main()
