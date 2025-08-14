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
from ..input import InputManager

_font: pygame.font.Font | None = None
_fonts: dict[int, pygame.font.Font] = {}
_default_size = 0
hover_hints: List[str] = []  # filled by tests; mirrors real project


# ---------------------------------------------------------------------------
# initialisation
# ---------------------------------------------------------------------------

def init_ui(scale: float = 1.0) -> None:
    """Initialise pygame font subsystem and cache a default font."""

    global _font, _fonts, _default_size
    if not pygame.font.get_init():  # pragma: no cover - defensive
        pygame.font.init()
    size = int(14 * max(1.0, min(scale, 2.0)))
    _font = pygame.font.SysFont(None, size)
    _fonts = {size: _font}
    _default_size = size


def _f(size: int | None = None) -> pygame.font.Font:
    assert _font is not None, "widgets.init_ui() must be called first"
    if size is None or size == _default_size:
        return _font
    if size not in _fonts:
        _fonts[size] = pygame.font.SysFont(None, size)
    return _fonts[size]


# ---------------------------------------------------------------------------
# modal dialogs (very small placeholders)
# ---------------------------------------------------------------------------


class ModalError:  # pragma: no cover - used in manual runs
    """Blocking error dialog with a *Copy details* button.

    ``details`` may contain an arbitrarily long traceback.  Only the last
    twenty lines are shown but the *Copy details* button (or pressing ``C``)
    copies the full text to the clipboard so bug reports can include the full
    stack trace.
    """

    def __init__(self, message: str, details: str) -> None:
        self.message = message
        self.details = details
        self.preview = "\n".join(details.splitlines()[-20:])
        self._btn_rect: pygame.Rect | None = None

    def run(self, surface: pygame.Surface) -> str:
        running = True
        clock = pygame.time.Clock()
        while running:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
                elif event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_c:
                        copy_to_clipboard(self.details)
                    elif event.key in (pygame.K_ESCAPE, pygame.K_RETURN):
                        running = False
                elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                    if self._btn_rect and self._btn_rect.collidepoint(event.pos):
                        copy_to_clipboard(self.details)
            surface.fill((0, 0, 0))
            y = 10
            img = _f().render(self.message, True, (255, 0, 0))
            surface.blit(img, (10, y))
            y += img.get_height() + 10
            for line in self.preview.splitlines():
                txt = _f().render(line, True, (255, 255, 255))
                surface.blit(txt, (10, y))
                y += txt.get_height() + 2
            btn_img = _f().render(_("copy_details"), True, (0, 0, 0))
            self._btn_rect = btn_img.get_rect(topleft=(10, y + 10))
            pygame.draw.rect(surface, (255, 255, 255), self._btn_rect.inflate(8, 6))
            surface.blit(btn_img, self._btn_rect)
            pygame.display.flip()
            clock.tick(30)
        return "quit"


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


class Dropdown:
    """Very small dropdown widget used in settings menus.

    The widget mirrors the style of other test widgets and purposefully keeps
    behaviour to a minimum – it merely lets the user pick a value from a list
    of options.  Each option is a ``(value, text)`` tuple and the currently
    selected value is available via :attr:`value`.
    """

    def __init__(
        self,
        rect: pygame.Rect,
        options: list[tuple[str, str]],
        value: str,
        callback: Callable[[str], None] | None = None,
    ) -> None:
        self.rect = pygame.Rect(rect)
        self.options = options
        self.value = value
        self.callback = callback
        self.open = False
        self.row_h = max(24, self.rect.height)
        self._hover = next((i for i, (v, _t) in enumerate(options) if v == value), 0)

    # drawing ----------------------------------------------------------
    def render(self, surface: pygame.Surface) -> None:  # pragma: no cover - visual
        theme = get_theme()
        colors = theme.colors
        # button -------------------------------------------------
        pygame.draw.rect(surface, colors["panel"], self.rect)
        pygame.draw.rect(surface, colors["border"], self.rect, theme.border_xs)
        label = next((t for v, t in self.options if v == self.value), str(self.value))
        img = _f().render(label, True, colors["text"])
        surface.blit(
            img,
            (self.rect.x + theme.padding, self.rect.y + (self.rect.height - img.get_height()) // 2),
        )

        if not self.open:
            return

        # options -------------------------------------------------
        for i, (val, text) in enumerate(self.options):
            opt_rect = pygame.Rect(
                self.rect.x,
                self.rect.bottom + i * self.row_h,
                self.rect.width,
                self.row_h,
            )
            if self.open:
                bg = colors["panel_hover"] if i == self._hover else colors["panel"]
            else:
                bg = colors["panel_hover"] if val == self.value else colors["panel"]
            pygame.draw.rect(surface, bg, opt_rect)
            pygame.draw.rect(surface, colors["border"], opt_rect, theme.border_xs)
            img = _f().render(text, True, colors["text"])
            surface.blit(
                img,
                (opt_rect.x + theme.padding, opt_rect.y + (opt_rect.height - img.get_height()) // 2),
            )

    # events -----------------------------------------------------------
    def handle_event(self, event: pygame.event.Event) -> None:
        if event.type == pygame.KEYDOWN and self.open:
            if event.key == pygame.K_UP:
                self._hover = (self._hover - 1) % len(self.options)
            elif event.key == pygame.K_DOWN:
                self._hover = (self._hover + 1) % len(self.options)
            elif event.key == pygame.K_RETURN:
                val = self.options[self._hover][0]
                if val != self.value:
                    self.value = val
                    if self.callback:
                        self.callback(val)
                self.open = False
            return
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if self.open:
                for i, (val, _text) in enumerate(self.options):
                    opt_rect = pygame.Rect(
                        self.rect.x,
                        self.rect.bottom + i * self.row_h,
                        self.rect.width,
                        self.row_h,
                    )
                    if opt_rect.collidepoint(event.pos):
                        if val != self.value:
                            self.value = val
                            if self.callback:
                                self.callback(val)
                        self.open = False
                        return
                if not self.rect.collidepoint(event.pos):
                    self.open = False
            elif self.rect.collidepoint(event.pos):
                self.open = True
                self._hover = next((i for i, (v, _t) in enumerate(self.options) if v == self.value), 0)

    def draw(self, surface: pygame.Surface) -> None:  # pragma: no cover - alias
        self.render(surface)


class Toggle:
    def __init__(self, label: str, rect: pygame.Rect, value: bool, on_change: Callable[[bool], None]) -> None:
        self.label = label
        self.rect = pygame.Rect(rect)
        self.value = value
        self.on_change = on_change

    def render(self, surface: pygame.Surface) -> None:  # pragma: no cover - visual
        theme = get_theme()
        colors = theme.colors
        pygame.draw.rect(surface, colors["panel"], self.rect)
        pygame.draw.rect(surface, colors["border"], self.rect, theme.border_xs)
        img = _f().render(self.label, True, colors["text"])
        surface.blit(
            img,
            (self.rect.x + theme.padding, self.rect.y + (self.rect.height - img.get_height()) // 2),
        )
        size = self.rect.height - 2 * theme.padding
        box = pygame.Rect(self.rect.right - size - theme.padding, self.rect.y + theme.padding, size, size)
        pygame.draw.rect(surface, colors["border"], box, theme.border_xs)
        if self.value:
            pygame.draw.rect(surface, get_theme().palette["ui"].accent, box.inflate(-4, -4))

    draw = render

    def handle_event(self, event: pygame.event.Event) -> None:
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1 and self.rect.collidepoint(event.pos):
            self.value = not self.value
            self.on_change(self.value)


class Slider:
    def __init__(
        self,
        rect: pygame.Rect,
        vmin: int,
        vmax: int,
        value: int | float,
        on_change: Callable[[float], None],
    ) -> None:
        self.rect = pygame.Rect(rect)
        self.vmin = float(vmin)
        self.vmax = float(vmax)
        self.value = float(value)
        self.on_change = on_change
        self._drag = False

    def _set_from_pos(self, x: int) -> None:
        rel = (x - self.rect.x) / self.rect.width
        rel = max(0.0, min(1.0, rel))
        self.value = self.vmin + rel * (self.vmax - self.vmin)
        self.on_change(self.value)

    def render(self, surface: pygame.Surface) -> None:  # pragma: no cover - visual
        theme = get_theme()
        colors = theme.colors
        pygame.draw.rect(surface, colors["panel"], self.rect)
        pygame.draw.rect(surface, colors["border"], self.rect, theme.border_xs)
        rel = (self.value - self.vmin) / (self.vmax - self.vmin)
        knob_x = self.rect.x + int(rel * self.rect.width)
        knob = pygame.Rect(knob_x - 4, self.rect.y, 8, self.rect.height)
        pygame.draw.rect(surface, get_theme().palette["ui"].accent, knob)

    draw = render

    def handle_event(self, event: pygame.event.Event) -> None:
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1 and self.rect.collidepoint(event.pos):
            self._drag = True
            self._set_from_pos(event.pos[0])
        elif event.type == pygame.MOUSEMOTION and self._drag:
            self._set_from_pos(event.pos[0])
        elif event.type == pygame.MOUSEBUTTONUP and event.button == 1 and self._drag:
            self._drag = False
        elif event.type == pygame.KEYDOWN:
            if event.key == pygame.K_LEFT:
                self.value = max(self.vmin, self.value - 1)
                self.on_change(self.value)
            elif event.key == pygame.K_RIGHT:
                self.value = min(self.vmax, self.value + 1)
                self.on_change(self.value)


class RebindButton:
    def __init__(self, rect: pygame.Rect, action: str, input: InputManager) -> None:
        self.rect = pygame.Rect(rect)
        self.action = action
        self.input = input
        self.listening = False

    def render(self, surface: pygame.Surface) -> None:  # pragma: no cover - visual
        theme = get_theme()
        colors = theme.colors
        pygame.draw.rect(surface, colors["panel"], self.rect)
        pygame.draw.rect(surface, colors["border"], self.rect, theme.border_xs)
        if self.listening:
            text = _("press_new_key")
        else:
            key = self.input.bindings.get(self.action)
            key_name = pygame.key.name(key) if key is not None else "?"
            text = f"{_(self.action)}: {key_name}"
        img = _f().render(text, True, colors["text"])
        surface.blit(img, (self.rect.x + theme.padding, self.rect.y + (self.rect.height - img.get_height()) // 2))

    draw = render

    def handle_event(self, event: pygame.event.Event) -> None:
        if self.listening and event.type == pygame.KEYDOWN:
            self.input.rebind(self.action, event.key)
            self.listening = False
        elif (
            event.type == pygame.MOUSEBUTTONDOWN
            and event.button == 1
            and self.rect.collidepoint(event.pos)
        ):
            self.listening = True


class LargeTextToggle(Toggle):
    def __init__(self, rect: pygame.Rect, value: bool, on_change: Callable[[bool], None]) -> None:
        super().__init__(_("large_text"), rect, value, on_change)
        self._font_size = int(_f().get_height() * 1.5)

    def render(self, surface: pygame.Surface) -> None:  # pragma: no cover - visual
        theme = get_theme()
        colors = theme.colors
        pygame.draw.rect(surface, colors["panel"], self.rect)
        pygame.draw.rect(surface, colors["border"], self.rect, theme.border_xs)
        img = _f(self._font_size).render(self.label, True, colors["text"])
        surface.blit(
            img,
            (self.rect.x + theme.padding, self.rect.y + (self.rect.height - img.get_height()) // 2),
        )
        size = self.rect.height - 2 * theme.padding
        box = pygame.Rect(self.rect.right - size - theme.padding, self.rect.y + theme.padding, size, size)
        pygame.draw.rect(surface, colors["border"], box, theme.border_xs)
        if self.value:
            pygame.draw.rect(surface, get_theme().palette["ui"].accent, box.inflate(-4, -4))

    draw = render


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
    "Dropdown",
    "Toggle",
    "Slider",
    "RebindButton",
    "LargeTextToggle",
    "HelpOverlay",
    "SubtitleBar",
    "Minimap",
    "MinimapWidget",
    "hover_hints",
]
