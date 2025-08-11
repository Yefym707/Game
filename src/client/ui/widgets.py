"""Small UI widgets used by the client."""
from __future__ import annotations

import pygame


class Button:
    """Clickable rectangular button."""

    def __init__(self, text: str, rect: pygame.Rect, callback) -> None:
        self.text = text
        self.rect = pygame.Rect(rect)
        self.callback = callback
        self.font = pygame.font.SysFont(None, 24)
        self.hover = False

    def handle_event(self, event: pygame.event.Event) -> None:
        if event.type == pygame.MOUSEMOTION:
            self.hover = self.rect.collidepoint(event.pos)
        elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if self.rect.collidepoint(event.pos):
                self.callback()

    def draw(self, surface: pygame.Surface) -> None:
        color = (100, 100, 100) if self.hover else (60, 60, 60)
        pygame.draw.rect(surface, color, self.rect)
        pygame.draw.rect(surface, (255, 255, 255), self.rect, 2)
        img = self.font.render(self.text, True, (255, 255, 255))
        surface.blit(img, img.get_rect(center=self.rect.center))


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
        text = f"Turn {state.turn}  Player {state.player.x},{state.player.y}"
        img = self.font.render(text, True, (255, 255, 0))
        surface.blit(img, (5, 5))
