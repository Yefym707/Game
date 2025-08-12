from __future__ import annotations

from pathlib import Path
import sys
from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / 'src'))

from tools import build_tiles
from gamecore import config as gconfig

ASSETS = ROOT / 'assets' / 'tiles'


def _ensure_tiles() -> None:
    if not ASSETS.exists():
        build_tiles.generate(ROOT / 'textures.json')


def _load_tile(symbol: str) -> Image.Image:
    name = build_tiles.escape_symbol(symbol) + '.png'
    return Image.open(ASSETS / name)


def _make_image(title: str) -> Image.Image:
    base = _load_tile('.')
    w, h = 800, 600
    img = Image.new('RGBA', (w, h))
    for y in range(0, h, base.height):
        for x in range(0, w, base.width):
            img.paste(base, (x, y))
    draw = ImageDraw.Draw(img)
    font = ImageFont.load_default()
    draw.text((20, 20), title, font=font, fill=(0, 0, 0))
    return img


def main() -> None:
    _ensure_tiles()
    out_dir = gconfig.screenshot_dir()
    out_dir.mkdir(parents=True, exist_ok=True)
    scenes = [
        ('menu', 'Menu'),
        ('battle', 'Battle'),
        ('minimap', 'MiniMap'),
        ('editor', 'MapEditor'),
    ]
    for name, title in scenes:
        img = _make_image(title)
        img.save(out_dir / f'{name}.png')
    print('screenshots saved to', out_dir)


if __name__ == '__main__':
    main()
