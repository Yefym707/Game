"""Scene allowing the player to pick a save slot."""
from __future__ import annotations

import time
import pygame

from gamecore import saveio
from gamecore.i18n import gettext as _
from .scene_base import Scene
from .ui.widgets import Button, ModalConfirm


class LoadScene(Scene):
    def __init__(self, app) -> None:
        super().__init__(app)
        self.confirm: ModalConfirm | None = None
        self._build_ui()

    def _build_ui(self) -> None:
        w, h = self.app.screen.get_size()
        self.entries: list[tuple[Button, Button]] = []
        saves = saveio.list_saves()
        for i, info in enumerate(saves):
            y = 40 + i * 50
            meta = info.get("meta", {})
            date = time.strftime("%Y-%m-%d", time.localtime(meta.get("modified", 0)))
            turn_txt = _("status_turn").format(turn=meta.get("turn", 0))
            seed_txt = f"{_('seed')}: {meta.get('seed', 0)}"
            text = f"{_('slot')} {info['slot']} - {date} - {turn_txt} {seed_txt}"
            load_btn = Button(
                text,
                pygame.Rect(40, y, 400, 32),
                lambda s=info["slot"]: self._load_slot(s),
            )
            del_btn = Button(
                _("delete"),
                pygame.Rect(450, y, 80, 32),
                lambda s=info["slot"]: self._ask_delete(s),
            )
            self.entries.append((load_btn, del_btn))
        self.back_btn = Button(_("BACK"), pygame.Rect(40, h - 60, 120, 40), self._back)
        self.focusables = [b for pair in self.entries for b in pair] + [self.back_btn]
        if self.focusables:
            self.focusables[0].focus = True
        self.focus_idx = 0

    # callbacks --------------------------------------------------------
    def _load_slot(self, slot: int) -> None:
        try:
            saveio.load(slot)
        except Exception:
            return
        from .scene_game import GameScene

        self.next_scene = GameScene(self.app, new_game=False)

    def _ask_delete(self, slot: int) -> None:
        w, h = self.app.screen.get_size()
        rect = pygame.Rect(w // 2 - 150, h // 2 - 75, 300, 150)

        def _do() -> None:
            saveio.delete(slot)
            self.confirm = None
            self._build_ui()

        self.confirm = ModalConfirm(rect, _("confirm_delete"), _do)

    def _back(self) -> None:
        from .scene_menu import MenuScene

        self.next_scene = MenuScene(self.app)

    # focus & events ---------------------------------------------------
    def _move_focus(self, step: int) -> None:
        if not self.focusables:
            return
        self.focusables[self.focus_idx].focus = False
        self.focus_idx = (self.focus_idx + step) % len(self.focusables)
        self.focusables[self.focus_idx].focus = True

    def handle_event(self, event: pygame.event.Event) -> None:
        if self.confirm:
            self.confirm.handle_event(event)
            return
        if event.type == pygame.KEYDOWN:
            if event.key in (pygame.K_TAB, pygame.K_DOWN):
                self._move_focus(1)
            elif event.key == pygame.K_UP:
                self._move_focus(-1)
        for w in self.focusables:
            w.handle_event(event)

    def update(self, dt: float) -> None:
        if self.confirm:
            self.confirm.update(dt)

    def draw(self, surface: pygame.Surface) -> None:
        surface.fill((0, 0, 0))
        for load_btn, del_btn in self.entries:
            load_btn.draw(surface)
            del_btn.draw(surface)
        self.back_btn.draw(surface)
        if self.confirm:
            self.confirm.draw(surface)

