import os
import sys
import pathlib

import pygame


ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.extend([str(ROOT), str(ROOT / "src")])

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
pygame.init()

from client.input_map import InputManager  # noqa: E402  pylint: disable=wrong-import-position
from client.ui import widgets  # noqa: E402  pylint: disable=wrong-import-position


def test_defaults_and_get_set() -> None:
    im = InputManager.from_config(None)
    assert im.get("move_up") == pygame.K_w
    im.set("end_turn", pygame.K_RETURN)
    assert im.get("end_turn") == pygame.K_RETURN


def test_serialization_roundtrip() -> None:
    im = InputManager.from_config(None)
    im.set("rest", pygame.K_x)
    cfg = im.to_config()
    im2 = InputManager.from_config(cfg)
    assert im2.get("rest") == pygame.K_x


def test_rebind_button_updates_manager() -> None:
    widgets.init_ui()
    im = InputManager.from_config(None)
    changed: list[tuple[str, int]] = []
    btn = widgets.RebindButton(pygame.Rect(0, 0, 100, 30), "end_turn", im, lambda a, k: changed.append((a, k)))
    btn.listening = True
    btn.handle_event(pygame.event.Event(pygame.KEYDOWN, key=pygame.K_z))
    assert im.get("end_turn") == pygame.K_z
    assert changed and changed[-1] == ("end_turn", pygame.K_z)

