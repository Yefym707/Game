"""Animated main menu scene."""
from __future__ import annotations

import pygame

from gamecore.i18n import gettext as _
from gamecore import achievements, rules
from .app import Scene
from .ui.widgets import Button, Card, NameField, ColorPicker
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

        # scenario / difficulty selectors --------------------------------
        self.scenarios = ["short", "medium", "long"]
        self.scenario_idx = self.scenarios.index(app.cfg.get("scenario", "short"))
        scen_text = _("scenario") + ": " + _(
            f"scenario_{self.scenarios[self.scenario_idx]}_name"
        )
        self.scenario_btn = Button(
            scen_text, pygame.Rect(20, 20, 200, 32), self._next_scenario
        )

        self.difficulties = ["easy", "normal", "hard"]
        self.diff_idx = self.difficulties.index(app.cfg.get("difficulty", "normal"))
        diff_text = _("difficulty") + ": " + _(self.difficulties[self.diff_idx])
        self.diff_btn = Button(
            diff_text, pygame.Rect(20, 60, 200, 32), self._next_difficulty
        )

        self.continue_btn = Button(
            _("CONTINUE"),
            pygame.Rect(w // 2 - 60, cy + card_h + 40, 120, 40),
            self._continue,
        )
        self.settings_btn = Button(
            _("SETTINGS"), pygame.Rect(w // 2 - 60, h - 80, 120, 40), self._settings
        )
        self.focusables = (
            [self.scenario_btn, self.diff_btn]
            + self.cards
            + [self.continue_btn, self.settings_btn]
        )
        if rules.DEMO_MODE:
            self.demo_btn = Button(
                _("PLAY_DEMO"),
                pygame.Rect(w // 2 - 60, cy + card_h + 90, 120, 40),
                self._start_demo,
            )
            self.focusables.append(self.demo_btn)
        self.focus_idx = 0
        self.focusables[0].focus = True
        self.bg_time = 0.0
        self.ach_font = pygame.font.Font(None, 20)

    # callbacks ---------------------------------------------------------
    def _start_mode(self, mode: str) -> None:
        if mode == "local":
            self.next_scene = LocalCoopScene(self.app)
            return
        if mode == "online":
            from .scene_online import OnlineScene

            self.next_scene = OnlineScene(self.app)
            return
        from .scene_game import GameScene

        self.app.cfg["scenario"] = self.scenarios[self.scenario_idx]
        self.app.cfg["difficulty"] = self.difficulties[self.diff_idx]
        self.next_scene = GameScene(self.app, new_game=True)

    def _start_demo(self) -> None:
        """Launch a new demo game."""

        from .scene_game import GameScene

        self.app.cfg["scenario"] = self.scenarios[self.scenario_idx]
        self.app.cfg["difficulty"] = self.difficulties[self.diff_idx]
        self.next_scene = GameScene(self.app, new_game=True)

    def _continue(self) -> None:
        from .scene_game import GameScene

        self.next_scene = GameScene(self.app, new_game=False)

    def _settings(self) -> None:
        from .scene_settings import SettingsScene

        self.next_scene = SettingsScene(self.app)

    def _next_scenario(self) -> None:
        """Cycle through available scenarios."""

        self.scenario_idx = (self.scenario_idx + 1) % len(self.scenarios)
        name = _(
            f"scenario_{self.scenarios[self.scenario_idx]}_name"
        )
        self.scenario_btn.text = f"{_('scenario')}: {name}"

    def _next_difficulty(self) -> None:
        """Cycle between easy/normal/hard."""

        self.diff_idx = (self.diff_idx + 1) % len(self.difficulties)
        name = _(self.difficulties[self.diff_idx])
        self.diff_btn.text = f"{_('difficulty')}: {name}"

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
        self.scenario_btn.draw(surface)
        self.diff_btn.draw(surface)
        for card in self.cards:
            card.draw(surface)
        self.continue_btn.draw(surface)
        self.settings_btn.draw(surface)
        if rules.DEMO_MODE:
            self.demo_btn.draw(surface)
        for i, (aid, unlocked, prog) in enumerate(achievements.list_achievements()):
            status = "✔" if unlocked else f"{int(prog * 100)}%"
            txt = f"{aid}: {status}"
            img = self.ach_font.render(txt, True, (255, 255, 255))
            surface.blit(img, (10, 10 + i * 20))


class LocalCoopScene(Scene):
    """Simple setup screen for local co-op."""

    def __init__(self, app) -> None:
        super().__init__(app)
        self.player_data = [{"name": "P1", "color": "red"}, {"name": "P2", "color": "blue"}]
        w, h = app.screen.get_size()
        self.start_btn = Button(_("PLAY"), pygame.Rect(w // 2 - 60, h - 60, 120, 40), self._start)
        self.inc_btn = Button("+", pygame.Rect(50, 50, 30, 30), self._inc)
        self.dec_btn = Button("-", pygame.Rect(90, 50, 30, 30), self._dec)
        self.fields: list[NameField] = []
        self.pickers: list[ColorPicker] = []
        self._rebuild_widgets()

    def _rebuild_widgets(self) -> None:
        self.fields.clear()
        self.pickers.clear()
        for i, pdata in enumerate(self.player_data):
            y = 100 + i * 50
            nf = NameField(pygame.Rect(100, y, 120, 30), pdata["name"], lambda t, i=i: self._set_name(i, t))
            cp = ColorPicker(pygame.Rect(230, y, 80, 30), pdata["color"], lambda c, i=i: self._set_color(i, c))
            self.fields.append(nf)
            self.pickers.append(cp)

    def _set_name(self, idx: int, text: str) -> None:
        self.player_data[idx]["name"] = text

    def _set_color(self, idx: int, color: str) -> None:
        self.player_data[idx]["color"] = color

    def _inc(self) -> None:
        if len(self.player_data) < 4:
            self.player_data.append({"name": f"P{len(self.player_data)+1}", "color": "red"})
            self._rebuild_widgets()

    def _dec(self) -> None:
        if len(self.player_data) > 2:
            self.player_data.pop()
            self._rebuild_widgets()

    def handle_event(self, event: pygame.event.Event) -> None:
        for w in self.fields + self.pickers + [self.start_btn, self.inc_btn, self.dec_btn]:
            w.handle_event(event)

    def update(self, dt: float) -> None:  # pragma: no cover - trivial
        pass

    def draw(self, surface: pygame.Surface) -> None:
        surface.fill((0, 0, 0))
        for w in self.fields + self.pickers:
            w.draw(surface)
        self.start_btn.draw(surface)
        self.inc_btn.draw(surface)
        self.dec_btn.draw(surface)

    def _start(self) -> None:
        self.app.cfg["players"] = list(self.player_data)
        from .scene_game import GameScene

        self.next_scene = GameScene(self.app, new_game=True)