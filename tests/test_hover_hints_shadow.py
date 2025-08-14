import os
import sys
import pathlib

import pygame

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.extend([str(ROOT), str(ROOT / "src")])

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
pygame.init()
pygame.font.init()

import client.ui.widgets as uiw  # noqa: E402  pylint: disable=wrong-import-position
from client.ui.widgets import HoverHints  # noqa: E402  pylint: disable=wrong-import-position


def test_hover_hints_shadow() -> None:
    uiw.init_ui()
    hints_list = []  # local variable should not shadow uiw.hover_hints
    surf = pygame.Surface((10, 10))
    uiw.hover_hints.show("tip", (0, 0))
    uiw.hover_hints.draw(surf)
    assert isinstance(uiw.hover_hints, HoverHints)
