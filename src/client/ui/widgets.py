"""Small UI widgets used by the client."""
from __future__ import annotations

import pygame

from ..sfx import ui_click
from gamecore.i18n import gettext as _


class Button:
    """Clickable rectangular button."""

    def __init__(self, text: str, rect: pygame.Rect, callback) -> None:
        self.text = text
        self.rect = pygame.Rect(rect)
        self.callback = callback
        self.font = pygame.font.SysFont(None, 24)
        self.hover = False
        self.focus = False

    def handle_event(self, event: pygame.event.Event) -> None:
        if event.type == pygame.MOUSEMOTION:
            self.hover = self.rect.collidepoint(event.pos)
        elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if self.rect.collidepoint(event.pos):
                ui_click()
                self.callback()
        elif event.type == pygame.KEYDOWN and self.focus:
            if event.key in (pygame.K_RETURN, pygame.K_SPACE):
                ui_click()
                self.callback()

    def draw(self, surface: pygame.Surface) -> None:
        color = (100, 100, 100) if (self.hover or self.focus) else (60, 60, 60)
        pygame.draw.rect(surface, color, self.rect)
        pygame.draw.rect(surface, (255, 255, 255), self.rect, 2)
        img = self.font.render(self.text, True, (255, 255, 255))
        surface.blit(img, img.get_rect(center=self.rect.center))


class Toggle(Button):
    """Simple on/off button."""

    def __init__(self, text: str, rect: pygame.Rect, value: bool, callback) -> None:
        super().__init__(text, rect, self._toggle)
        self.value = value
        self.callback = callback
        self._update()

    def _toggle(self) -> None:
        self.value = not self.value
        self._update()
        self.callback(self.value)

    def _update(self) -> None:
        self.text = f"{self.text.split(':')[0]}: {'on' if self.value else 'off'}"


class Card(Button):
    """Large button styled as a card with a short description."""

    def __init__(self, title: str, desc: str, rect: pygame.Rect, callback) -> None:
        super().__init__(title, rect, callback)
        self.desc = desc
        self.font_small = pygame.font.SysFont(None, 18)

    def draw(self, surface: pygame.Surface) -> None:
        color = (80, 80, 120) if (self.hover or self.focus) else (40, 40, 60)
        pygame.draw.rect(surface, color, self.rect, border_radius=8)
        pygame.draw.rect(surface, (255, 255, 255), self.rect, 2, border_radius=8)
        title_img = self.font.render(self.text, True, (255, 255, 255))
        surface.blit(title_img, title_img.get_rect(center=(self.rect.centerx, self.rect.top + 30)))
        desc_img = self.font_small.render(self.desc, True, (200, 200, 200))
        surface.blit(desc_img, desc_img.get_rect(center=(self.rect.centerx, self.rect.top + 60)))


class Slider:
    """Horizontal slider used for volume/UI scale."""

    def __init__(self, rect: pygame.Rect, min_val: float, max_val: float, value: float, callback) -> None:
        self.rect = pygame.Rect(rect)
        self.min = min_val
        self.max = max_val
        self.value = value
        self.callback = callback
        self.grabbed = False

    def handle_event(self, event: pygame.event.Event) -> None:
        if event.type == pygame.MOUSEBUTTONDOWN and self.rect.collidepoint(event.pos):
            self.grabbed = True
            self._set_from_pos(event.pos[0])
        elif event.type == pygame.MOUSEBUTTONUP:
            self.grabbed = False
        elif event.type == pygame.MOUSEMOTION and self.grabbed:
            self._set_from_pos(event.pos[0])

    def _set_from_pos(self, x: int) -> None:
        rel = max(0.0, min(1.0, (x - self.rect.left) / self.rect.width))
        self.value = self.min + rel * (self.max - self.min)
        self.callback(self.value)

    def draw(self, surface: pygame.Surface) -> None:
        pygame.draw.rect(surface, (80, 80, 80), self.rect)
        rel = (self.value - self.min) / (self.max - self.min)
        knob_x = int(self.rect.left + rel * self.rect.width)
        pygame.draw.rect(surface, (160, 160, 160), pygame.Rect(knob_x - 3, self.rect.top, 6, self.rect.height))


class Dropdown:
    """Cycle-through dropdown used for language selection."""

    def __init__(self, rect: pygame.Rect, options: list[str], value: str, callback) -> None:
        self.rect = pygame.Rect(rect)
        self.options = options
        self.value = value
        self.callback = callback
        self.font = pygame.font.SysFont(None, 24)

    def handle_event(self, event: pygame.event.Event) -> None:
        if event.type == pygame.MOUSEBUTTONDOWN and self.rect.collidepoint(event.pos):
            idx = (self.options.index(self.value) + 1) % len(self.options)
            self.value = self.options[idx]
            self.callback(self.value)

    def draw(self, surface: pygame.Surface) -> None:
        pygame.draw.rect(surface, (60, 60, 60), self.rect)
        pygame.draw.rect(surface, (255, 255, 255), self.rect, 2)
        img = self.font.render(self.value, True, (255, 255, 255))
        surface.blit(img, img.get_rect(center=self.rect.center))


class RebindButton(Button):
    """Button waiting for next key press to rebind an action."""

    def __init__(self, rect: pygame.Rect, action: str, manager, label: str | None = None) -> None:
        text = label or action
        super().__init__(text, rect, self._begin)
        self.action = action
        self.manager = manager
        self.waiting = False
        self._update()

    def _begin(self) -> None:
        self.waiting = True
        self.text = _("press_key")

    def _finish(self, key: int) -> None:
        self.manager.rebind(self.action, key)
        self.waiting = False
        self._update()

    def _update(self) -> None:
        key = self.manager.bindings.get(self.action, 0)
        self.text = f"{self.action}: {pygame.key.name(key)}"

    def handle_event(self, event: pygame.event.Event) -> None:
        if self.waiting and event.type == pygame.KEYDOWN:
            self._finish(event.key)
        else:
            super().handle_event(event)


class Log:
    """Scrolling log widget."""

    def __init__(self, max_lines: int = 20) -> None:
        self.lines = []
        self.max_lines = max_lines
        self.font = pygame.font.SysFont(None, 18)

    def add(self, msg: str) -> None:
        self.lines.append(msg)
        if len(self.lines) > self.max_lines:
            self.lines = self.lines[-self.max_lines :]

    def draw(self, surface: pygame.Surface, rect: pygame.Rect) -> None:
        pygame.draw.rect(surface, (30, 30, 30), rect)
        pygame.draw.rect(surface, (80, 80, 80), rect, 1)
        y = rect.top + 5
        for line in self.lines[-self.max_lines :]:
            img = self.font.render(line, True, (200, 200, 200))
            surface.blit(img, (rect.left + 5, y))
            y += self.font.get_linesize()


class StatusPanel:
    """Renders basic game state info at the top-left."""

    def __init__(self) -> None:
        self.font = pygame.font.SysFont(None, 24)

    def draw(self, surface: pygame.Surface, state) -> None:
        text = _("status_turn").format(turn=state.turn, x=state.player.x, y=state.player.y)
        img = self.font.render(text, True, (255, 255, 0))
        surface.blit(img, (5, 5))
