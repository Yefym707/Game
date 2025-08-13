from __future__ import annotations

"""Simple modal dialog shown when a cloud save conflicts with a local one."""

import os
import pygame
from pathlib import Path

from gamecore import config as gconfig
from gamecore.i18n import gettext as _
from .scene_base import Scene
from .ui.widgets import Button


class SaveConflictScene(Scene):
    """Very small scene allowing the user to pick a save version."""

    def __init__(self, app, local_meta, cloud_meta, save_path: Path):
        super().__init__(app)
        self.local_meta = local_meta
        self.cloud_meta = cloud_meta
        self.save_path = save_path
        self.choice: str | None = None
        w, h = app.screen.get_size()
        cx = w // 2 - 100
        cy = h // 2 - 60
        self.btn_local = Button(_("local_version"), pygame.Rect(cx, cy, 200, 40), lambda: self._choose("local"))
        self.btn_cloud = Button(_("cloud_version"), pygame.Rect(cx, cy + 50, 200, 40), lambda: self._choose("cloud"))
        self.btn_alocal = Button(
            _("always_prefer_local"),
            pygame.Rect(cx, cy + 100, 200, 40),
            lambda: self._always("prefer_local"),
        )
        self.btn_acloud = Button(
            _("always_prefer_cloud"),
            pygame.Rect(cx, cy + 150, 200, 40),
            lambda: self._always("prefer_cloud"),
        )
        self.btn_backups = Button(
            _("open_backups_folder"),
            pygame.Rect(cx, cy + 200, 200, 40),
            self._open_backups,
        )
        self.widgets = [
            self.btn_local,
            self.btn_cloud,
            self.btn_alocal,
            self.btn_acloud,
            self.btn_backups,
        ]

    def _choose(self, choice: str) -> None:
        self.choice = choice
        self.app.pop_scene(choice)

    def _always(self, policy: str) -> None:
        self.app.cfg["save_conflict_policy"] = policy
        gconfig.save_config(self.app.cfg)
        self._choose("local" if policy == "prefer_local" else "cloud")

    def _open_backups(self) -> None:
        bdir = gconfig.CONFIG_DIR / "backups"
        os.makedirs(bdir, exist_ok=True)
        try:
            os.startfile(str(bdir))  # type: ignore[attr-defined]
        except Exception:
            pass

    def handle_event(self, event: pygame.event.Event) -> None:
        for w in self.widgets:
            w.handle_event(event)

    def draw(self, surface: pygame.Surface) -> None:
        surface.fill((20, 20, 20))
        for w in self.widgets:
            w.draw(surface)
