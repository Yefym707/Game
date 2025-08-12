"""Animated main menu scene."""
from __future__ import annotations

import pygame

from gamecore.i18n import gettext as _
from .app import Scene
from .ui.widgets import Button, Card
from .sfx import set_volume


class MenuScene(Scene):
    """Modernised main menu with animated background and mode cards."""

    def __init__(self, app) -> None:
        super().__init__(app)
        set_volume(app.cfg.get("volume", 1.0))
        w, h = app.screen.get_size()
        scale = app.cfg.get("ui_scale", 1.0)
        card_w, card_h = int(200 * scale), int(120 * scale)
        spacing = int(20 * scale)
        cx = w // 2 - card_w - spacing
        cy = h // 2 - card_h // 2
        self.cards: list[Card] = []

        def add(key: str, desc_key: str, cb) -> None:
            rect = pygame.Rect(0, 0, card_w, card_h)
            rect.topleft = (
                cx + len(self.cards) * (card_w + spacing),
                cy,
            )
            self.cards.append(Card(_(key), _(desc_key), rect, cb))

        add("SOLO", "PLAY", lambda: self._start_mode("solo"))
        add("LOCAL_COOP", "PLAY", lambda: self._start_mode("local"))
        add("ONLINE", "PLAY", lambda: self._start_mode("online"))

        self.continue_btn = Button(
            _("CONTINUE"),
            pygame.Rect(w // 2 - 60, cy + card_h + 40, 120, 40),
            self._continue,
        )
        self.settings_btn = Button(
            _("SETTINGS"), pygame.Rect(w // 2 - 60, h - 80, 120, 40), self._settings
        )
        self.focusables = self.cards + [self.continue_btn, self.settings_btn]
        self.focus_idx = 0
        self.focusables[0].focus = True
        self.bg_time = 0.0

    # callbacks ---------------------------------------------------------
    def _start_mode(self, mode: str) -> None:
        from .scene_game import GameScene

        self.next_scene = GameScene(self.app, new_game=True)

    def _continue(self) -> None:
        from .scene_game import GameScene

        self.next_scene = GameScene(self.app, new_game=False)

    def _settings(self) -> None:
        from .scene_settings import SettingsScene

        self.next_scene = SettingsScene(self.app)

    # event handling ----------------------------------------------------
    def _move_focus(self, step: int) -> None:
        self.focusables[self.focus_idx].focus = False
        self.focus_idx = (self.focus_idx + step) % len(self.focusables)
        self.focusables[self.focus_idx].focus = True

    def handle_event(self, event: pygame.event.Event) -> None:
        if event.type == pygame.KEYDOWN:
            if event.key in (pygame.K_RIGHT, pygame.K_DOWN):
                self._move_focus(1)
            elif event.key in (pygame.K_LEFT, pygame.K_UP):
                self._move_focus(-1)
        for w in self.focusables:
            w.handle_event(event)

    # update / draw ----------------------------------------------------
    def update(self, dt: float) -> None:
        self.bg_time += dt

    def _draw_bg(self, surface: pygame.Surface) -> None:
        surface.fill((10, 10, 30))
        w, h = surface.get_size()
        for i, color in enumerate([(30, 30, 50), (40, 40, 70), (50, 50, 90)]):
            size = 40 * (i + 1)
            off = (self.bg_time * 20 * (i + 1)) % size
            for x in range(-size, w, size):
                pygame.draw.line(surface, color, (x + off, 0), (x + off, h))
            for y in range(-size, h, size):
                pygame.draw.line(surface, color, (0, y + off), (w, y + off))

    def draw(self, surface: pygame.Surface) -> None:
        self._draw_bg(surface)
        for card in self.cards:
            card.draw(surface)
        self.continue_btn.draw(surface)
        self.settings_btn.draw(surface)
