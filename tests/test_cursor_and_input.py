import sys
import pathlib

import pytest


BASE = pathlib.Path(__file__).resolve().parents[1]
if str(BASE / "src") not in sys.path:
    sys.path.insert(0, str(BASE / "src"))


def test_cursor_and_input(monkeypatch):
    pygame = pytest.importorskip("pygame")
    monkeypatch.setenv("SDL_VIDEODRIVER", "dummy")
    monkeypatch.setenv("SDL_AUDIODRIVER", "dummy")
    pygame.init(); pygame.display.init(); pygame.font.init()

    from client.app import App

    app = App()
    assert pygame.mouse.get_visible()
    assert app.input_map.map_event(
        pygame.event.Event(pygame.MOUSEBUTTONDOWN, button=1)
    ) == "select"

    evt = pygame.event.Event(pygame.KEYDOWN, key=pygame.K_F1)
    app.handle_event(evt)
    assert app.help.visible

