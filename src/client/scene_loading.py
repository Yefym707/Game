"""Loading screen scene."""
from __future__ import annotations

import random
import pygame
from typing import Callable, Iterable

from gamecore import i18n
from gamecore.i18n import gettext as _
from .async_loader import AsyncLoader


class LoadingScene:
    """Display a loading screen while preparing resources."""

    def __init__(self, app: "App", loader: AsyncLoader | None = None, next_scene_cls: Callable[["App"], object] | None = None) -> None:
        self.app = app
        self.next_scene: object | None = None
        if next_scene_cls is None:
            from .scene_menu import MenuScene

            next_scene_cls = MenuScene
        self._next_scene_cls = next_scene_cls

        if loader is None:
            tasks: list[Callable[[], Iterable[None] | None]] = [
                self._load_config,
                self._load_locales,
                self._prepare_assets,
            ]
            loader = AsyncLoader(tasks, app.cfg.get("loader_batch_ms", 8))
        self.loader = loader
        tips = i18n.safe_get("tips", [])
        self.tip = random.choice(tips) if tips else ""

    # default loader tasks -------------------------------------------------
    def _load_config(self) -> None:
        from gamecore import config as gconfig

        gconfig.load_config()

    def _load_locales(self) -> None:
        i18n.set_language(self.app.cfg.get("lang", "en"))

    def _prepare_assets(self) -> None:
        # Placeholder for other startup tasks like tile generation
        return None

    # scene interface ------------------------------------------------------
    def update(self, dt: float) -> None:  # noqa: D401 - part of interface
        self.loader.step()
        if self.loader.done:
            self.next_scene = self._next_scene_cls(self.app)

    def draw(self, surface: pygame.Surface) -> None:  # noqa: D401
        surface.fill((0, 0, 0))
        progress = self.loader.progress
        txt = self.app.font.render(f"{_('loading')} {int(progress)}%", True, (255, 255, 255))
        surface.blit(txt, (20, 20))
        if self.tip:
            tip_label = self.app.font.render(f"{_('tips')}: {self.tip}", True, (200, 200, 200))
            surface.blit(tip_label, (20, 60))

