from __future__ import annotations

import random
from pathlib import Path
import sys
from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from tools import build_tiles

ASSETS = ROOT / 'assets' / 'tiles'


def _ensure_tiles() -> None:
    if not ASSETS.exists():
        build_tiles.generate(ROOT / 'textures.json')


def main() -> None:
    _ensure_tiles()
    tiles = list(ASSETS.glob('*.png'))
    random.shuffle(tiles)
    cols = 5
    rows = 3
    tile_size = 64
    img = Image.new('RGBA', (cols * tile_size, rows * tile_size))
    for idx, path in enumerate(tiles[: cols * rows ]):
        tile = Image.open(path)
        x = (idx % cols) * tile_size
        y = (idx // cols) * tile_size
        img.paste(tile, (x, y))
    draw = ImageDraw.Draw(img)
    font = ImageFont.load_default()
    text = 'OKO vs Zombies'
    bbox = draw.textbbox((0, 0), text, font=font)
    tw, th = bbox[2] - bbox[0], bbox[3] - bbox[1]
    draw.text(((img.width - tw) // 2, img.height - th - 10), text, font=font, fill=(0, 0, 0))
    draw.rectangle([(0, 0), (img.width - 1, img.height - 1)], outline=(0, 0, 0), width=3)
    out = ROOT / 'keyart.png'
    img.save(out)
    print('key art saved to', out)


if __name__ == '__main__':
    main()
