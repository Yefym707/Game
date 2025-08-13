from __future__ import annotations

"""Small collection of widgets used in tests.

The goal of this module is not to be a full UI framework but merely to provide
light‑weight stand ins for the game.  Widgets expose just enough behaviour so
unit tests can instantiate and draw them without crashing.
"""

from dataclasses import dataclass
from typing import Callable, List

import pygame

from gamecore.i18n import gettext as _
from ..clipboard import copy as copy_to_clipboard
from ..gfx.tileset import TILE_SIZE
from .theme import get_theme

_font: pygame.font.Font | None = None
hover_hints: List[str] = []  # filled by tests; mirrors real project


# ---------------------------------------------------------------------------
# initialisation
# ---------------------------------------------------------------------------

def init_ui(scale: float = 1.0) -> None:
    """Initialise pygame font subsystem and cache a default font."""

    global _font
    if not pygame.font.get_init():  # pragma: no cover - defensive
        pygame.font.init()
    size = int(14 * max(1.0, min(scale, 2.0)))
    _font = pygame.font.SysFont(None, size)


def _f() -> pygame.font.Font:
    assert _font is not None, "widgets.init_ui() must be called first"
    return _font


# ---------------------------------------------------------------------------
# modal dialogs (very small placeholders)
# ---------------------------------------------------------------------------


class ModalError:  # pragma: no cover - used in manual runs
    """Very small blocking error dialog.

    The dialog shows ``message`` and allows copying ``details`` to the clipboard
    by pressing ``C``.  It returns ``"quit"`` once the user dismisses the dialog
    so calling code can exit cleanly.
    """

    def __init__(self, message: str, details: str) -> None:
        self.message = message
        self.details = details

    def run(self, surface: pygame.Surface) -> str:
        running = True
        clock = pygame.time.Clock()
        result = "quit"
        while running:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
                elif event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_c:
                        copy_to_clipboard(self.details)
                    elif event.key in (pygame.K_ESCAPE, pygame.K_RETURN):
                        running = False
            surface.fill((0, 0, 0))
            img = _f().render(self.message, True, (255, 0, 0))
            surface.blit(img, (10, 10))
            hint = _f().render(_("copy_details"), True, (255, 255, 255))
            surface.blit(hint, (10, 40))
            pygame.display.flip()
            clock.tick(30)
        return result


class ModalConfirm:
    def __init__(self, message: str, on_yes: Callable[[], None]) -> None:
        self.message = message
        self._on_yes = on_yes

    def on_yes(self) -> None:
        self._on_yes()

    def handle_event(self, event: pygame.event.Event) -> None:  # pragma: no cover - minimal
        if event.type == pygame.KEYDOWN and event.key == pygame.K_RETURN:
            self.on_yes()

    def update(self, dt: float) -> None:  # pragma: no cover - placeholder
        pass

    def draw(self, surf: pygame.Surface) -> None:  # pragma: no cover - visual
        img = _f().render(self.message, True, (255, 255, 255))
        rect = img.get_rect(center=surf.get_rect().center)
        pygame.draw.rect(surf, (0, 0, 0), rect.inflate(20, 20))
        surf.blit(img, rect)


# ---------------------------------------------------------------------------
# basic widgets
# ---------------------------------------------------------------------------

@dataclass
class Panel:
    rect: pygame.Rect

    def draw(self, surf: pygame.Surface) -> None:  # pragma: no cover - visual
        pygame.draw.rect(surf, (50, 50, 50), self.rect, 1)


class Card(Panel):
    pass


@dataclass
class Label:
    text: str
    rect: pygame.Rect

    def draw(self, surf: pygame.Surface) -> None:  # pragma: no cover - visual
        img = _f().render(self.text, True, (255, 255, 255))
        surf.blit(img, self.rect)


@dataclass
class Button(Label):
    callback: Callable[[], None]

    def handle_event(self, event: pygame.event.Event) -> None:
        if event.type == pygame.MOUSEBUTTONDOWN and self.rect.collidepoint(event.pos):
            self.callback()


class Toast:
    def __init__(self, text: str) -> None:
        self.text = text

    def draw(self, surf: pygame.Surface, y: int) -> None:  # pragma: no cover - visual
        img = _f().render(self.text, True, (255, 255, 255))
        rect = img.get_rect(midtop=(surf.get_width() // 2, y))
        pygame.draw.rect(surf, (0, 0, 0), rect.inflate(10, 10))
        surf.blit(img, rect)


class Tooltip:
    def __init__(self, text: str) -> None:
        self.text = text

    def draw(self, surf: pygame.Surface, pos) -> None:  # pragma: no cover - visual
        img = _f().render(self.text, True, (0, 0, 0))
        rect = img.get_rect(topleft=pos)
        pygame.draw.rect(surf, (250, 250, 210), rect.inflate(4, 4))
        surf.blit(img, rect)


# ---------------------------------------------------------------------------
# help overlay and minimap
# ---------------------------------------------------------------------------

class HelpOverlay:
    def __init__(self, input_map) -> None:
        self.visible = False
        self.input_map = input_map

    def toggle(self) -> None:
        self.visible = not self.visible

    def draw(self, surf: pygame.Surface) -> None:  # pragma: no cover - visual
        if not self.visible:
            return
        lines = hover_hints or []
        y = 10
        for line in lines:
            img = _f().render(line, True, (255, 255, 255))
            surf.blit(img, (10, y))
            y += img.get_height() + 2


class SubtitleBar:
    """Tiny subtitle helper used in accessibility tests."""

    def __init__(self) -> None:
        self.text: str | None = None

    def show(self, text: str) -> None:
        self.text = text

    def update(self, dt: float) -> None:  # pragma: no cover - placeholder
        pass

    def draw(self, surf: pygame.Surface) -> None:  # pragma: no cover - visual
        if not self.text:
            return
        img = _f().render(self.text, True, (255, 255, 255))
        rect = img.get_rect(midbottom=(surf.get_width() // 2, surf.get_height()))
        pygame.draw.rect(surf, (0, 0, 0), rect.inflate(10, 10))
        surf.blit(img, rect)


class Minimap:
    """Very small clickable minimap.

    It only tracks a reference to the camera and board size.  A click inside the
    minimap converts the coordinates to world space and asks the camera to
    ``jump_to`` the new location.
    """

    def __init__(self, rect: pygame.Rect, board_size: tuple[int, int], camera) -> None:
        self.rect = rect
        self.board_w, self.board_h = board_size
        self.camera = camera

    def draw(self, surf: pygame.Surface) -> None:  # pragma: no cover - visual
        pygame.draw.rect(surf, (80, 80, 80), self.rect, 1)
        # draw current view rectangle
        vw = self.camera.screen_w / self.camera.world_w * self.rect.width
        vh = self.camera.screen_h / self.camera.world_h * self.rect.height
        vx = self.rect.x + (self.camera.x / self.camera.world_w) * self.rect.width
        vy = self.rect.y + (self.camera.y / self.camera.world_h) * self.rect.height
        pygame.draw.rect(surf, (255, 255, 255), pygame.Rect(vx, vy, vw, vh), 1)

    def handle_event(self, event: pygame.event.Event) -> None:
        if event.type == pygame.MOUSEBUTTONDOWN and self.rect.collidepoint(event.pos):
            relx = (event.pos[0] - self.rect.x) / self.rect.width
            rely = (event.pos[1] - self.rect.y) / self.rect.height
            cell = (int(relx * self.board_w), int(rely * self.board_h))
            self.camera.jump_to((cell[0] * TILE_SIZE, cell[1] * TILE_SIZE))


class MinimapWidget:
    """Clickable minimap rendering a board onto an internal surface.

    The widget pre-renders the ``board`` onto a private :class:`Surface` so the
    draw call simply scales that surface into ``rect``.  Players and zombies are
    drawn as coloured rectangles using the active theme's palette.  Clicking
    inside the widget converts the position into board coordinates and centres
    the camera on that cell.
    """

    def __init__(self, rect: pygame.Rect, board, camera) -> None:
        self.rect = rect
        self.board = board
        self.camera = camera
        self.surface = pygame.Surface((board.width, board.height))
        pal = get_theme().palette["ui"]
        self.legend = {
            ".": (180, 180, 180),
            "#": (60, 60, 60),
            "player": pal.accent,
            "zombie": pal.danger,
        }
        self._render_map()

    # internal ---------------------------------------------------------
    def _render_map(self) -> None:
        for y, row in enumerate(self.board.tiles):
            for x, ch in enumerate(row):
                self.surface.set_at((x, y), self.legend.get(ch, self.legend["."]))

    # drawing ----------------------------------------------------------
    def draw(self, surf: pygame.Surface) -> None:  # pragma: no cover - visual
        img = pygame.transform.scale(self.surface, self.rect.size)
        surf.blit(img, self.rect.topleft)
        scale_x = self.rect.width / self.board.width
        scale_y = self.rect.height / self.board.height
        # entities
        for p in getattr(self.board, "players", []):
            px = self.rect.x + p.x * scale_x
            py = self.rect.y + p.y * scale_y
            pygame.draw.rect(
                surf,
                self.legend["player"],
                pygame.Rect(px, py, max(1, scale_x), max(1, scale_y)),
            )
        for z in getattr(self.board, "zombies", []):
            px = self.rect.x + z.x * scale_x
            py = self.rect.y + z.y * scale_y
            pygame.draw.rect(
                surf,
                self.legend["zombie"],
                pygame.Rect(px, py, max(1, scale_x), max(1, scale_y)),
            )
        # view rectangle
        theme = get_theme()
        vw = self.camera.screen_w / self.camera.world_w * self.rect.width
        vh = self.camera.screen_h / self.camera.world_h * self.rect.height
        vx = self.rect.x + (self.camera.x / self.camera.world_w) * self.rect.width
        vy = self.rect.y + (self.camera.y / self.camera.world_h) * self.rect.height
        pygame.draw.rect(
            surf,
            theme.palette["ui"].neutral,
            pygame.Rect(vx, vy, vw, vh),
            theme.border_xs,
        )

    # events -----------------------------------------------------------
    def handle_event(self, event: pygame.event.Event) -> None:
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1 and self.rect.collidepoint(event.pos):
            relx = (event.pos[0] - self.rect.x) / self.rect.width
            rely = (event.pos[1] - self.rect.y) / self.rect.height
            cell = (int(relx * self.board.width), int(rely * self.board.height))
            self.camera.jump_to((cell[0] * TILE_SIZE, cell[1] * TILE_SIZE))


__all__ = [
    "init_ui",
    "ModalError",
    "ModalConfirm",
    "Panel",
    "Card",
    "Label",
    "Button",
    "Toast",
    "Tooltip",
    "HelpOverlay",
    "SubtitleBar",
    "Minimap",
    "MinimapWidget",
    "hover_hints",
]
