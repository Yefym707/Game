"""Minimal new game setup wizard.

The full project ships with a fairly feature rich setup dialog.  For the unit
tests and manual runs in this kata we implement a condensed version that still
exposes the most common options: game mode, player names, difficulty and random
seed.  Navigation is keyboard driven and intentionally linear so the code stays
compact.  Pressing :kbd:`Enter` advances to the next step and the arrow keys
cycle through available choices.  Once all questions are answered the game
starts immediately by switching to :class:`scene_game.GameScene`.
"""

from __future__ import annotations

import random
from typing import List

import pygame

from gamecore.i18n import gettext as _
from gamecore import config as gconfig

from .scene_base import Scene


class NewGameScene(Scene):
    def __init__(self, app) -> None:
        super().__init__(app)
        self._font = pygame.font.SysFont(None, 24)

        cfg = gconfig.load_config()
        self.mode_index = 0
        self.modes = ["newgame_solo", "newgame_local_coop"]
        self.player_count = 1
        self.names: List[str] = cfg.get("default_player_names", ["P1", "P2", "P3", "P4"])
        self.difficulties = ["easy", "normal", "hard"]
        self.diff_index = 1
        self.seed = cfg.get("last_seed", random.randint(0, 999999))

        self.step = 0

    # helpers -----------------------------------------------------------
    def _start(self) -> None:
        from .scene_game import GameScene

        self.app.cfg["last_seed"] = self.seed
        gconfig.save_config(self.app.cfg)
        self.next_scene = GameScene(self.app)

    # scene interface ---------------------------------------------------
    def handle_event(self, event: pygame.event.Event) -> None:  # pragma: no cover - simple
        if event.type != pygame.KEYDOWN:
            return
        if event.key == pygame.K_RETURN:
            if self.step >= 4:
                self._start()
            else:
                self.step += 1
            return
        if event.key in (pygame.K_UP, pygame.K_RIGHT):
            delta = 1
        elif event.key in (pygame.K_DOWN, pygame.K_LEFT):
            delta = -1
        else:
            return
        if self.step == 0:
            self.mode_index = (self.mode_index + delta) % len(self.modes)
            self.player_count = 1 if self.mode_index == 0 else max(2, self.player_count)
        elif self.step == 1:
            self.player_count = max(1, min(4, self.player_count + delta))
        elif self.step == 2:
            self.diff_index = (self.diff_index + delta) % len(self.difficulties)
        elif self.step == 3:
            self.seed = (self.seed + delta) % 1_000_000

    def update(self, dt: float) -> None:  # pragma: no cover - nothing to update
        pass

    def draw(self, surface: pygame.Surface) -> None:  # pragma: no cover - visual
        surface.fill((0, 0, 0))
        w = surface.get_width()
        h = surface.get_height()
        lines = []
        if self.step == 0:
            lines.append(_("newgame_mode") + f": {_(self.modes[self.mode_index])}")
        elif self.step == 1:
            lines.append(_("newgame_players") + f": {self.player_count}")
            for i in range(self.player_count):
                lines.append(f"{i+1}. {self.names[i]}")
        elif self.step == 2:
            lines.append(_("newgame_difficulty") + f": {_(self.difficulties[self.diff_index])}")
        elif self.step == 3:
            lines.append(_("newgame_seed") + f": {self.seed:06d}")
            lines.append(_("newgame_seed_hint"))
        else:
            lines.append(_("newgame_start_hint"))

        for i, text in enumerate(lines):
            img = self._font.render(text, True, (255, 255, 255))
            rect = img.get_rect(center=(w // 2, h // 2 + i * 30))
            surface.blit(img, rect)


__all__ = ["NewGameScene"]

