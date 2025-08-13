from __future__ import annotations

import sys
import pathlib
import types

import pytest

BASE = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(BASE / "src"))
sys.path.insert(0, str(BASE))


def test_loading_flow(monkeypatch, tmp_path):
    pygame = pytest.importorskip("pygame")
    monkeypatch.setenv("SDL_VIDEODRIVER", "dummy")
    monkeypatch.setenv("SDL_AUDIODRIVER", "dummy")
    monkeypatch.setenv("HOME", str(tmp_path))
    pygame.init()
    pygame.font.init()

    # stub menu scene to avoid heavy imports
    stub_menu = types.ModuleType("client.scene_menu")
    stub_menu.MenuScene = object
    sys.modules["client.scene_menu"] = stub_menu

    from client.scene_loading import LoadingScene
    from client.async_loader import AsyncLoader

    class DummyApp:
        def __init__(self) -> None:
            self.cfg = {"loader_batch_ms": 1}
            self.font = pygame.font.SysFont(None, 16)
            self.screen = pygame.Surface((100, 100))

    app = DummyApp()

    steps: list[int] = []

    def make_task(n: int):
        def _task():
            steps.append(n)
            yield
        return _task

    tasks = [make_task(i) for i in range(5)]
    loader = AsyncLoader(tasks, batch_ms=1)
    scene = LoadingScene(app, loader=loader, next_scene_cls=lambda a: object())

    progresses = []
    while not loader.done:
        progresses.append(loader.progress)
        scene.update(0.016)

    assert steps == list(range(5))
    assert progresses[0] == 0.0
    assert loader.progress == 100.0

