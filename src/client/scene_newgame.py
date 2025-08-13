"""Setup wizard for starting a new game."""
from __future__ import annotations

import random
import pygame

from gamecore import scenario as gscenario, rules, config as gconfig
from gamecore.i18n import gettext as _
from .scene_base import Scene
from .ui.widgets import Button, NameField


class NewGameScene(Scene):
    """Collect basic parameters before launching the game."""

    def __init__(self, app) -> None:
        super().__init__(app)
        w, h = app.screen.get_size()
        self.modes = ["SOLO", "LOCAL_COOP"]
        self.mode_idx = 0
        self.mode_btn = Button("", pygame.Rect(40, 40, 220, 32), self._toggle_mode)
        self.player_count = 1
        self.player_btn = Button("", pygame.Rect(40, 80, 220, 32), self._cycle_players)
        self.default_names = app.cfg.get("default_player_names", [])
        self.name_fields: list[NameField] = []
        self._rebuild_names()
        self.difficulties = ["easy", "normal", "hard"]
        self.diff_idx = 1
        self.diff_btn = Button("", pygame.Rect(40, 200, 220, 32), self._next_diff)
        scenarios = gscenario.load_scenarios()
        self.scenarios = list(scenarios.keys())
        self.scen_idx = 0
        self.scen_btn = Button("", pygame.Rect(40, 240, 220, 32), self._next_scen)
        seed = str(app.cfg.get("last_seed", 0))
        self.seed_field = NameField(pygame.Rect(40, 280, 140, 32), seed, lambda t: None)
        self.rand_btn = Button(_("random"), pygame.Rect(190, 280, 70, 32), self._random_seed)
        self.start_btn = Button(_("PLAY"), pygame.Rect(w - 240, h - 60, 200, 40), self._start)
        self.back_btn = Button(_("BACK"), pygame.Rect(40, h - 60, 120, 40), self._back)
        self._update_texts()
        self.focusables = [
            self.mode_btn,
            self.player_btn,
            *self.name_fields,
            self.diff_btn,
            self.scen_btn,
            self.seed_field,
            self.rand_btn,
            self.start_btn,
            self.back_btn,
        ]
        self.focus_idx = 0
        self.focusables[0].focus = True

    # helpers ----------------------------------------------------------
    def _update_texts(self) -> None:
        self.mode_btn.text = f"{_('mode')}: {_(self.modes[self.mode_idx])}"
        self.player_btn.text = f"{_('num_players')}: {self.player_count}"
        diff = _(self.difficulties[self.diff_idx])
        self.diff_btn.text = f"{_('difficulty')}: {diff}"
        scen_name = _(
            f"scenario_{self.scenarios[self.scen_idx]}_name"
        )
        self.scen_btn.text = f"{_('scenario')}: {scen_name}"

    def _rebuild_names(self) -> None:
        self.name_fields.clear()
        for i in range(self.player_count):
            name = self.default_names[i] if i < len(self.default_names) else f"P{i+1}"
            field = NameField(
                pygame.Rect(40, 120 + i * 32, 220, 32),
                name,
                lambda t, idx=i: None,
            )
            self.name_fields.append(field)

    # callbacks --------------------------------------------------------
    def _toggle_mode(self) -> None:
        self.mode_idx = 1 - self.mode_idx
        if self.mode_idx == 0:
            self.player_count = 1
        else:
            self.player_count = max(self.player_count, 2)
        self._rebuild_names()
        self._update_texts()

    def _cycle_players(self) -> None:
        if self.mode_idx == 0:
            self.player_count = 1
        else:
            self.player_count = self.player_count % 4 + 1
            if self.player_count < 2:
                self.player_count = 2
        self._rebuild_names()
        self._update_texts()

    def _next_diff(self) -> None:
        self.diff_idx = (self.diff_idx + 1) % len(self.difficulties)
        self._update_texts()

    def _next_scen(self) -> None:
        self.scen_idx = (self.scen_idx + 1) % len(self.scenarios)
        self._update_texts()

    def _random_seed(self) -> None:
        self.seed_field.text = str(random.randint(0, 999999))

    def _start(self) -> None:
        seed = int(self.seed_field.text or 0)
        rules.set_seed(seed)
        players = []
        for field in self.name_fields:
            players.append({"name": field.text})
        self.app.cfg["players"] = players
        self.app.cfg["scenario"] = self.scenarios[self.scen_idx]
        self.app.cfg["difficulty"] = self.difficulties[self.diff_idx]
        cfg = gconfig.load_config()
        cfg["last_seed"] = seed
        if cfg.get("last_used_slot") is None:
            cfg["last_used_slot"] = 1
        gconfig.save_config(cfg)
        from .scene_game import GameScene

        self.next_scene = GameScene(self.app, new_game=True)

    def _back(self) -> None:
        from .scene_menu import MenuScene

        self.next_scene = MenuScene(self.app)

    # focus / events ---------------------------------------------------
    def _move_focus(self, step: int) -> None:
        self.focusables[self.focus_idx].focus = False
        self.focus_idx = (self.focus_idx + step) % len(self.focusables)
        self.focusables[self.focus_idx].focus = True

    def handle_event(self, event: pygame.event.Event) -> None:
        if event.type == pygame.KEYDOWN:
            if event.key in (pygame.K_TAB, pygame.K_DOWN):
                self._move_focus(1)
            elif event.key == pygame.K_UP:
                self._move_focus(-1)
        for w in self.focusables:
            w.handle_event(event)

    def update(self, dt: float) -> None:  # pragma: no cover - trivial
        pass

    def draw(self, surface: pygame.Surface) -> None:
        surface.fill((0, 0, 0))
        for w in self.focusables:
            w.draw(surface)

