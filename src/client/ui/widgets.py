"""Small UI widgets used by the client."""
from __future__ import annotations

import pygame

from ..sfx import ui_click
from .. import clipboard
from gamecore.i18n import gettext as _
from .theme import get_theme
from ..input import DEFAULT_GAMEPAD


class ModalError:
    """Very small modal dialog used for crash reporting.

    The dialog shows ``message`` and optional ``details`` and offers a list of
    ``buttons`` where each item is ``(id, label)``.  ``run`` returns the id of
    the pressed button.  If a button with id ``"copy"`` is supplied the
    ``details`` text is copied to the clipboard when pressed.
    """

    def __init__(
        self,
        message: str,
        details: str | None,
        buttons: list[tuple[str, str]],
    ) -> None:
        self.message = message
        self.details = details
        self.buttons = buttons
        self.font = pygame.font.SysFont(None, 24)

    def run(self, surface: pygame.Surface) -> str:
        th = get_theme()
        btn_rects: list[tuple[str, pygame.Rect]] = []
        while True:
            surface.fill((0, 0, 0))
            msg = self.font.render(self.message, True, th.colors["text"])
            surface.blit(msg, (20, 20))
            y = 60
            btn_rects.clear()
            for bid, label in self.buttons:
                rect = pygame.Rect(20, y, 160, 30)
                pygame.draw.rect(surface, th.colors["panel"], rect, border_radius=th.radius)
                pygame.draw.rect(surface, th.colors["border"], rect, 2, border_radius=th.radius)
                img = self.font.render(label, True, th.colors["text"])
                surface.blit(img, img.get_rect(center=rect.center))
                btn_rects.append((bid, rect))
                y += 40
            pygame.display.flip()
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    return "quit"
                if event.type == pygame.KEYDOWN:
                    if event.key in (pygame.K_ESCAPE, pygame.K_q):
                        return "quit"
                    if event.key in (pygame.K_RETURN, pygame.K_r):
                        return "restart"
                    if event.key == pygame.K_c and self.details:
                        clipboard.copy(self.details)
                if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                    for bid, rect in btn_rects:
                        if rect.collidepoint(event.pos):
                            if bid == "copy" and self.details:
                                clipboard.copy(self.details)
                                break
                            return bid



class HoverHints:
    """Collect hover rectangles and draw tooltips."""

    def __init__(self) -> None:
        self.items: list[tuple[pygame.Rect, str]] = []
        self.font = pygame.font.SysFont(None, 18)

    def add(self, rect: pygame.Rect, text: str) -> None:
        self.items.append((pygame.Rect(rect), text))

    def draw(self, surface: pygame.Surface) -> None:
        if not self.items:
            return
        th = get_theme()
        pos = pygame.mouse.get_pos()
        for rect, text in self.items:
            if rect.collidepoint(pos):
                img = self.font.render(text, True, th.colors["text"])
                hint_rect = img.get_rect(topleft=(pos[0] + th.padding, pos[1] + th.padding))
                bg_rect = hint_rect.inflate(th.padding * 2, th.padding * 2)
                pygame.draw.rect(
                    surface,
                    th.colors["tooltip"],
                    bg_rect,
                    border_radius=th.radius,
                )
                surface.blit(img, hint_rect)
                break
        self.items.clear()


hover_hints = HoverHints()


class FocusRing:
    """Draw a ring around a widget to indicate keyboard focus."""

    def __init__(self, rect: pygame.Rect) -> None:
        self.rect = pygame.Rect(rect)

    def draw(self, surface: pygame.Surface) -> None:
        th = get_theme()
        pygame.draw.rect(
            surface,
            th.palette["ui"].accent,
            self.rect.inflate(4, 4),
            th.border_xs,
            border_radius=th.radius_md,
        )


class HoverOutline:
    """Thin outline used on mouse hover."""

    def __init__(self, rect: pygame.Rect) -> None:
        self.rect = pygame.Rect(rect)

    def draw(self, surface: pygame.Surface) -> None:
        th = get_theme()
        pygame.draw.rect(
            surface,
            th.palette["ui"].neutral,
            self.rect.inflate(2, 2),
            th.border_xs,
            border_radius=th.radius_sm,
        )


class LegendWidget:
    """Display a list of colored squares with labels."""

    def __init__(self, items: list[tuple[tuple[int, int, int], str]], rect: pygame.Rect) -> None:
        self.items = items
        self.rect = pygame.Rect(rect)
        self.font = pygame.font.SysFont(None, 16)

    def draw(self, surface: pygame.Surface) -> None:
        th = get_theme()
        x, y = self.rect.topleft
        size = 10
        for color, label in self.items:
            square = pygame.Rect(x, y, size, size)
            surface.fill(color, square)
            pygame.draw.rect(surface, th.colors["border"], square, 1)
            img = self.font.render(label, True, th.colors["text"])
            surface.blit(img, (x + size + th.padding, y - 2))
            y += size + th.padding


class Panel:
    """Simple container with rounded corners and a subtle drop shadow."""

    def __init__(self, rect: pygame.Rect) -> None:
        self.rect = pygame.Rect(rect)

    def handle_event(self, event: pygame.event.Event) -> None:  # pragma: no cover - non interactive
        pass

    def draw(self, surface: pygame.Surface) -> None:
        th = get_theme()
        shadow1 = th.colors.get("shadow1", (0, 0, 0, 120))
        shadow2 = th.colors.get("shadow2", (0, 0, 0, 60))
        for off, col in ((4, shadow2), (2, shadow1)):
            sh = pygame.Surface(self.rect.size, pygame.SRCALPHA)
            pygame.draw.rect(sh, col, sh.get_rect(), border_radius=th.radius)
            surface.blit(sh, (self.rect.x + off, self.rect.y + off))
        pygame.draw.rect(surface, th.colors["panel"], self.rect, border_radius=th.radius)


class Label:
    """Non-interactive text label."""

    def __init__(self, text: str, rect: pygame.Rect) -> None:
        self.text = text
        self.rect = pygame.Rect(rect)
        self.font = pygame.font.SysFont(None, 24)

    def handle_event(self, event: pygame.event.Event) -> None:  # pragma: no cover - static
        pass

    def draw(self, surface: pygame.Surface) -> None:
        th = get_theme()
        img = self.font.render(self.text, True, th.colors["text"])
        surface.blit(img, self.rect.topleft)


class Button:
    """Clickable rectangular button."""

    def __init__(
        self,
        text: str,
        rect: pygame.Rect,
        callback,
        hint: str | None = None,
    ) -> None:
        self.text = text
        self.rect = pygame.Rect(rect)
        self.callback = callback
        self.font = pygame.font.SysFont(None, 24)
        self.hover = False
        self.focus = False
        self.hint = hint

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
        th = get_theme()
        color = th.colors["panel_hover"] if (self.hover or self.focus) else th.colors["panel"]
        pygame.draw.rect(surface, color, self.rect, border_radius=th.radius)
        pygame.draw.rect(surface, th.colors["border"], self.rect, 2, border_radius=th.radius)
        img = self.font.render(self.text, True, th.colors["text"])
        surface.blit(img, img.get_rect(center=self.rect.center))
        if self.hint:
            hover_hints.add(self.rect, self.hint)


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


class LargeTextToggle(Toggle):
    """Toggle that enlarges its label when enabled."""

    def __init__(self, rect: pygame.Rect, value: bool, callback) -> None:
        super().__init__(_("large_text"), rect, value, callback)
        self.base_font = pygame.font.SysFont(None, 24)
        self.large_font = pygame.font.SysFont(None, 32)
        self.font = self.large_font if value else self.base_font

    def _update(self) -> None:  # type: ignore[override]
        super()._update()
        self.font = self.large_font if self.value else self.base_font


class Card(Button):
    """Large button styled as a card with a short description."""

    def __init__(self, title: str, desc: str, rect: pygame.Rect, callback) -> None:
        super().__init__(title, rect, callback)
        self.desc = desc
        self.font_small = pygame.font.SysFont(None, 18)

    def draw(self, surface: pygame.Surface) -> None:
        th = get_theme()
        shadow1 = th.colors.get("shadow1", (0, 0, 0, 120))
        shadow2 = th.colors.get("shadow2", (0, 0, 0, 60))
        for off, col in ((6, shadow2), (3, shadow1)):
            sh = pygame.Surface(self.rect.size, pygame.SRCALPHA)
            pygame.draw.rect(sh, col, sh.get_rect(), border_radius=th.radius_lg)
            surface.blit(sh, (self.rect.x + off, self.rect.y + off))
        color = th.colors["panel_hover"] if (self.hover or self.focus) else th.colors["panel"]
        pygame.draw.rect(surface, color, self.rect, border_radius=th.radius_lg)
        pygame.draw.rect(surface, th.colors["border"], self.rect, th.border_width, border_radius=th.radius_lg)
        title_img = self.font.render(self.text, True, th.colors["text"])
        surface.blit(title_img, title_img.get_rect(center=(self.rect.centerx, self.rect.top + 30)))
        desc_img = self.font_small.render(self.desc, True, th.palette["ui"].neutral)
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
        th = get_theme()
        pygame.draw.rect(surface, th.colors["panel"], self.rect, border_radius=th.radius)
        rel = (self.value - self.min) / (self.max - self.min)
        knob_x = int(self.rect.left + rel * self.rect.width)
        pygame.draw.rect(
            surface,
            th.colors["panel_hover"],
            pygame.Rect(knob_x - 3, self.rect.top, 6, self.rect.height),
        )


class Dropdown:
    """Cycle-through dropdown used for language/theme selection."""

    def __init__(
        self,
        rect: pygame.Rect,
        options: list[tuple[str, str]] | list[str],
        value: str,
        callback,
    ) -> None:
        self.rect = pygame.Rect(rect)
        if options and isinstance(options[0], tuple):
            self.values = [o[0] for o in options]
            self.labels = [o[1] for o in options]
        else:
            self.values = list(options)  # type: ignore[arg-type]
            self.labels = list(options)  # type: ignore[arg-type]
        self.value = value
        self.callback = callback
        self.font = pygame.font.SysFont(None, 24)

    def handle_event(self, event: pygame.event.Event) -> None:
        if event.type == pygame.MOUSEBUTTONDOWN and self.rect.collidepoint(event.pos):
            idx = (self.values.index(self.value) + 1) % len(self.values)
            self.value = self.values[idx]
            self.callback(self.value)

    def draw(self, surface: pygame.Surface) -> None:
        th = get_theme()
        pygame.draw.rect(surface, th.colors["panel"], self.rect, border_radius=th.radius)
        pygame.draw.rect(
            surface,
            th.colors["border"],
            self.rect,
            th.border_width,
            border_radius=th.radius,
        )
        label = self.labels[self.values.index(self.value)]
        img = self.font.render(label, True, th.colors["text"])
        surface.blit(img, img.get_rect(center=self.rect.center))


class Tag:
    """Small label used to display values such as latency."""

    def __init__(self, text: str, rect: pygame.Rect) -> None:
        self.text = text
        self.rect = pygame.Rect(rect)
        self.font = pygame.font.SysFont(None, 18)

    def set_text(self, text: str) -> None:
        self.text = text

    def draw(self, surface: pygame.Surface) -> None:
        th = get_theme()
        pygame.draw.rect(surface, th.colors["panel"], self.rect, border_radius=th.radius)
        img = self.font.render(self.text, True, th.colors["text"])
        surface.blit(img, img.get_rect(center=self.rect.center))


class ConfirmDialog:
    """Very small yes/no confirmation dialog."""

    def __init__(self, rect: pygame.Rect, text: str, on_yes, on_no) -> None:
        self.rect = pygame.Rect(rect)
        self.text = text
        self.on_yes = on_yes
        self.on_no = on_no
        self.font = pygame.font.SysFont(None, 24)
        self.visible = False

    def show(self) -> None:
        self.visible = True

    def hide(self) -> None:
        self.visible = False

    def handle_event(self, event: pygame.event.Event) -> None:
        if not self.visible:
            return
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_y:
                self.on_yes()
                self.hide()
            elif event.key == pygame.K_n:
                self.on_no()
                self.hide()

    def draw(self, surface: pygame.Surface) -> None:
        if not self.visible:
            return
        th = get_theme()
        pygame.draw.rect(surface, th.colors["panel"], self.rect, border_radius=th.radius)
        img = self.font.render(self.text, True, th.colors["text"])
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
        text = _("status_turn").format(turn=state.turn)
        img = self.font.render(text, True, (255, 255, 0))
        surface.blit(img, (5, 5))
        active = _("active_player").format(name=state.current.name)
        img2 = self.font.render(active, True, (255, 255, 255))
        surface.blit(img2, (5, 30))


# ---------------------------------------------------------------------------
# Additional widgets used for UX polish


class Tooltip:
    """Simple text tooltip displayed near the cursor."""

    def __init__(self, text: str) -> None:
        self.text = text[:60]
        self.font = pygame.font.SysFont(None, 18)

    def draw(self, surface: pygame.Surface, pos: tuple[int, int]) -> None:
        th = get_theme()
        padding = th.padding
        img = self.font.render(self.text, True, th.colors["text"])
        text_rect = img.get_rect()
        bg_rect = text_rect.inflate(padding * 2, padding * 2)
        bg_rect.topleft = pos
        shadow1 = th.colors.get("shadow1", (0, 0, 0, 120))
        shadow2 = th.colors.get("shadow2", (0, 0, 0, 60))
        sh = pygame.Surface((bg_rect.width, bg_rect.height + 6), pygame.SRCALPHA)
        pygame.draw.rect(sh, shadow1, pygame.Rect(2, 2, bg_rect.width, bg_rect.height), border_radius=th.radius)
        pygame.draw.rect(sh, shadow2, pygame.Rect(4, 4, bg_rect.width, bg_rect.height), border_radius=th.radius)
        surface.blit(sh, bg_rect.topleft)
        pygame.draw.rect(surface, th.colors["tooltip"], bg_rect, border_radius=th.radius)
        arrow = [
            (bg_rect.centerx - 6, bg_rect.bottom),
            (bg_rect.centerx + 6, bg_rect.bottom),
            (bg_rect.centerx, bg_rect.bottom + 6),
        ]
        pygame.draw.polygon(surface, shadow1, [(x + 2, y + 2) for x, y in arrow])
        pygame.draw.polygon(surface, th.colors["tooltip"], arrow)
        surface.blit(img, (bg_rect.x + padding, bg_rect.y + padding))


class IconLabel:
    """Render ``icon`` and ``text`` side by side using unicode icons."""

    def __init__(self, icon: str, text: str) -> None:
        self.icon = icon
        self.text = text
        self.font = pygame.font.SysFont(None, 18)

    def draw(self, surface: pygame.Surface, pos: tuple[int, int]) -> None:
        th = get_theme()
        img = self.font.render(f"{self.icon} {self.text}", True, th.colors["text"])
        surface.blit(img, pos)


class IconLog:
    """Compact log with optional collapse/expand and small icons."""

    def __init__(self, max_lines: int = 20) -> None:
        self.entries: list[tuple[str, str]] = []
        self.max_lines = max_lines
        self.font = pygame.font.SysFont(None, 18)
        self.collapsed = False
        self.toggle_rect: pygame.Rect | None = None

    def add(self, icon: str, text: str) -> None:
        self.entries.append((icon, text))
        if len(self.entries) > self.max_lines:
            self.entries = self.entries[-self.max_lines :]

    def handle_event(self, event: pygame.event.Event) -> None:
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if self.toggle_rect and self.toggle_rect.collidepoint(event.pos):
                self.collapsed = not self.collapsed

    def draw(self, surface: pygame.Surface, rect: pygame.Rect) -> None:
        th = get_theme()
        pygame.draw.rect(surface, th.colors["panel"], rect)
        pygame.draw.rect(surface, th.colors["border"], rect, 1)
        # collapse/expand button
        icon = "▶" if self.collapsed else "◀"
        self.toggle_rect = pygame.Rect(rect.right - 20, rect.top, 20, 20)
        img = self.font.render(icon, True, th.colors["text"])
        surface.blit(img, self.toggle_rect.topleft)
        if self.collapsed:
            return
        y = rect.top + 5
        for ic, msg in self.entries[-self.max_lines :]:
            img = self.font.render(f"{ic} {msg}", True, th.colors["text"])
            surface.blit(img, (rect.left + 5, y))
            y += self.font.get_linesize()


class Panel:
    """Base panel supporting slide and fade animations."""

    def __init__(self, rect: pygame.Rect, from_side: str = "left") -> None:
        self.rect = pygame.Rect(rect)
        self.target = pygame.Rect(rect)
        self.from_side = from_side
        screen = pygame.display.get_surface()
        sw = screen.get_width() if screen else 0
        if from_side == "left":
            self.rect.x = -self.rect.width
        elif from_side == "right":
            self.rect.x = sw
        self.alpha = 0.0
        self.speed = 600.0

    def update(self, dt: float) -> None:
        if self.from_side == "left":
            self.rect.x = min(self.rect.x + self.speed * dt, self.target.x)
        else:
            self.rect.x = max(self.rect.x - self.speed * dt, self.target.x)
        self.alpha = min(255.0, self.alpha + self.speed * dt)

    def _draw_bg(self, surface: pygame.Surface) -> None:
        th = get_theme()
        panel = pygame.Surface(self.rect.size, pygame.SRCALPHA)
        panel.set_alpha(int(self.alpha))
        pygame.draw.rect(panel, th.colors["panel"], panel.get_rect(), border_radius=th.radius)
        pygame.draw.rect(panel, th.colors["border"], panel.get_rect(), 2, border_radius=th.radius)
        surface.blit(panel, self.rect.topleft)


class Toast:
    """Small message that fades out after a short duration."""

    def __init__(self, text: str, duration: float = 2.0) -> None:
        self.text = text
        self.duration = duration
        self.elapsed = 0.0
        self.font = pygame.font.SysFont(None, 24)

    def update(self, dt: float) -> bool:
        self.elapsed += dt
        return self.elapsed >= self.duration

    def draw(self, surface: pygame.Surface, y: int) -> None:
        th = get_theme()
        alpha = 255
        if self.elapsed > self.duration - 1.0:
            alpha = int(255 * (self.duration - self.elapsed))
        img = self.font.render(self.text, True, th.colors["text"])
        rect = img.get_rect(center=(surface.get_width() // 2, y))
        bg = pygame.Surface(rect.inflate(10, 10).size, pygame.SRCALPHA)
        bg.fill((*th.colors["toast"], alpha))
        surface.blit(bg, rect.inflate(10, 10).topleft)
        surface.blit(img, rect)


class ToastManager:
    """Manage a queue of active toasts."""

    def __init__(self) -> None:
        self.toasts: list[Toast] = []

    def show(self, text: str, duration: float = 2.0) -> None:
        text = text[:60]
        self.toasts.append(Toast(text, duration))
        if len(self.toasts) > 5:
            self.toasts = self.toasts[-5:]

    def update(self, dt: float) -> None:
        self.toasts = [t for t in self.toasts if not t.update(dt)]

    def draw(self, surface: pygame.Surface) -> None:
        y = surface.get_height() - 40
        for t in reversed(self.toasts):
            t.draw(surface, y)
            y -= 40


class ModalConfirm(Panel):
    """Simple modal confirmation dialog with yes/no buttons."""

    def __init__(self, rect: pygame.Rect, text: str, on_yes, on_no=None) -> None:
        super().__init__(rect, from_side="right")
        self.text = text
        self.on_yes = on_yes
        self.on_no = on_no
        self.font = pygame.font.SysFont(None, 24)
        bw = (self.rect.width - 60) // 2
        by = self.rect.bottom - 60
        self.btn_yes = Button(_("yes"), pygame.Rect(self.rect.left + 20, by, bw, 40), self._yes)
        self.btn_no: Button | None = None
        if on_no is not None:
            self.btn_no = Button(
                _("no"), pygame.Rect(self.rect.left + 40 + bw, by, bw, 40), self._no
            )

    def _yes(self) -> None:
        self.on_yes()

    def _no(self) -> None:
        if self.on_no:
            self.on_no()

    def handle_event(self, event: pygame.event.Event) -> None:
        self.btn_yes.handle_event(event)
        if self.btn_no:
            self.btn_no.handle_event(event)

    def update(self, dt: float) -> None:
        super().update(dt)

    def draw(self, surface: pygame.Surface) -> None:
        self._draw_bg(surface)
        th = get_theme()
        img = self.font.render(self.text, True, th.colors["text"])
        surface.blit(img, img.get_rect(center=(self.rect.centerx, self.rect.top + 40)))
        self.btn_yes.draw(surface)
        if self.btn_no:
            self.btn_no.draw(surface)


class PopupDialog(Panel):
    """Modal popup displaying text and choice buttons."""

    def __init__(self, rect: pygame.Rect, icon: str, title: str, desc: str, choices) -> None:
        super().__init__(rect, from_side="right")
        self.icon = icon
        self.title = title
        self.desc = desc
        self.font = pygame.font.SysFont(None, 24)
        self.font_small = pygame.font.SysFont(None, 18)
        bx = self.rect.left + 20
        by = self.rect.bottom - 50 * len(choices) - 20
        bw = self.rect.width - 40
        bh = 40
        self.buttons = [
            Button(text, pygame.Rect(bx, by + i * 50, bw, bh), cb)
            for i, (text, cb) in enumerate(choices)
        ]

    def handle_event(self, event: pygame.event.Event) -> None:
        for b in self.buttons:
            b.handle_event(event)

    def update(self, dt: float) -> None:
        super().update(dt)

    def draw(self, surface: pygame.Surface) -> None:
        self._draw_bg(surface)
        icon_img = self.font.render(self.icon, True, (255, 255, 0))
        surface.blit(icon_img, (self.rect.left + 5, self.rect.top + 5))
        th = get_theme()
        title_img = self.font.render(self.title, True, th.colors["text"])
        surface.blit(title_img, (self.rect.left + 40, self.rect.top + 5))
        desc_img = self.font_small.render(self.desc, True, th.colors["text"])
        surface.blit(desc_img, desc_img.get_rect(center=(self.rect.centerx, self.rect.top + 60)))
        for b in self.buttons:
            b.draw(surface)


class PauseMenu(Panel):
    """Overlay pause menu with basic options."""

    def __init__(self, rect: pygame.Rect, callbacks) -> None:
        super().__init__(rect, from_side="left")
        bx = self.rect.left + 20
        by = self.rect.top + 20
        bw = self.rect.width - 40
        bh = 40
        self.buttons = [
            Button(_("resume"), pygame.Rect(bx, by, bw, bh), callbacks.get("resume")),
            Button(_("restart"), pygame.Rect(bx, by + 50, bw, bh), callbacks.get("restart")),
            Button(_("SETTINGS"), pygame.Rect(bx, by + 100, bw, bh), callbacks.get("settings")),
            Button(_("menu_quit"), pygame.Rect(bx, by + 150, bw, bh), callbacks.get("exit")),
        ]

    def handle_event(self, event: pygame.event.Event) -> None:
        for b in self.buttons:
            b.handle_event(event)

    def update(self, dt: float) -> None:
        super().update(dt)

    def draw(self, surface: pygame.Surface) -> None:
        self._draw_bg(surface)
        for b in self.buttons:
            b.draw(surface)


class TimelineSlider(Slider):
    """Specialised slider used for replay timeline."""

    pass  # CONTINUE


class PlayPauseButton(Button):
    """Small helper button for play/pause."""

    def toggle(self) -> None:
        pass  # CONTINUE


class TilePalette:
    """Horizontal list of selectable tiles for the map editor."""

    def __init__(self, tiles: list[str], rect: pygame.Rect, cell: int = 32) -> None:
        self.tiles = tiles
        self.rect = pygame.Rect(rect)
        self.cell = cell
        self.selected = tiles[0] if tiles else "."
        self.font = pygame.font.SysFont(None, 18)

    def handle_event(self, event: pygame.event.Event) -> None:
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if self.rect.collidepoint(event.pos):
                idx = (event.pos[0] - self.rect.x) // self.cell
                if 0 <= idx < len(self.tiles):
                    self.selected = self.tiles[idx]

    def draw(self, surface: pygame.Surface) -> None:
        for i, tile in enumerate(self.tiles):
            r = pygame.Rect(self.rect.x + i * self.cell, self.rect.y, self.cell, self.cell)
            color = (120, 120, 120) if tile == self.selected else (80, 80, 80)
            pygame.draw.rect(surface, color, r)
            pygame.draw.rect(surface, (255, 255, 255), r, 1)
            img = self.font.render(tile, True, (0, 0, 0))
            surface.blit(img, img.get_rect(center=r.center))


class Toolbar:
    """Simple container for buttons used in the sandbox editor."""

    def __init__(self, buttons: list[Button]) -> None:
        self.buttons = buttons

    def handle_event(self, event: pygame.event.Event) -> None:
        for btn in self.buttons:
            btn.handle_event(event)

    def draw(self, surface: pygame.Surface) -> None:
        for btn in self.buttons:
            btn.draw(surface)


class NameField:
    """Very small text input widget for player names."""

    def __init__(self, rect: pygame.Rect, text: str, callback) -> None:
        self.rect = pygame.Rect(rect)
        self.text = text
        self.callback = callback
        self.font = pygame.font.SysFont(None, 24)
        self.active = False

    def handle_event(self, event: pygame.event.Event) -> None:
        if event.type == pygame.MOUSEBUTTONDOWN:
            self.active = self.rect.collidepoint(event.pos)
        elif event.type == pygame.KEYDOWN and self.active:
            if event.key == pygame.K_RETURN:
                self.callback(self.text)
                self.active = False
            elif event.key == pygame.K_BACKSPACE:
                self.text = self.text[:-1]
            else:
                self.text += event.unicode

    def draw(self, surface: pygame.Surface) -> None:
        pygame.draw.rect(surface, (60, 60, 60), self.rect)
        pygame.draw.rect(surface, (255, 255, 255), self.rect, 1)
        img = self.font.render(self.text, True, (255, 255, 255))
        surface.blit(img, (self.rect.x + 4, self.rect.y + 4))


class ColorPicker:
    """Cycle through a small set of colors."""

    COLORS = ["red", "green", "blue", "yellow"]

    def __init__(self, rect: pygame.Rect, color: str, callback) -> None:
        self.rect = pygame.Rect(rect)
        self.index = self.COLORS.index(color) if color in self.COLORS else 0
        self.callback = callback
        self.font = pygame.font.SysFont(None, 24)

    def handle_event(self, event: pygame.event.Event) -> None:
        if event.type == pygame.MOUSEBUTTONDOWN and self.rect.collidepoint(event.pos):
            self.index = (self.index + 1) % len(self.COLORS)
            self.callback(self.COLORS[self.index])

    def draw(self, surface: pygame.Surface) -> None:
        color_name = self.COLORS[self.index]
        pygame.draw.rect(surface, pygame.Color(color_name), self.rect)
        pygame.draw.rect(surface, (255, 255, 255), self.rect, 1)
        img = self.font.render(color_name, True, (0, 0, 0))
        surface.blit(img, img.get_rect(center=self.rect.center))


class SubtitleBar:
    """Display short event descriptions at the bottom of the screen."""

    def __init__(self) -> None:
        self.text = ""
        self.timer = 0.0
        self.font = pygame.font.SysFont(None, 24)
        self.dyslexia = False

    def show(self, text: str, dyslexia: bool = False) -> None:
        self.text = text
        self.timer = 3.0
        self.dyslexia = dyslexia

    def update(self, dt: float) -> None:
        if self.timer > 0:
            self.timer -= dt
            if self.timer <= 0:
                self.text = ""

    def draw(self, surface: pygame.Surface) -> None:
        if not self.text:
            return
        th = get_theme()
        display = self.text if not self.dyslexia else " ".join(self.text)
        img = self.font.render(display, True, th.colors["text"])
        rect = img.get_rect(center=(surface.get_width() // 2, surface.get_height() - 30))
        bg = rect.inflate(th.padding * 2, th.padding * 2)
        pygame.draw.rect(surface, th.colors["panel"], bg, border_radius=th.radius)
        pygame.draw.rect(surface, th.colors["border"], bg, th.border_width, border_radius=th.radius)
        surface.blit(img, rect)


class HelpOverlay:
    """Overlay listing current keyboard and gamepad controls."""

    def __init__(self, input_mgr) -> None:
        self.input = input_mgr
        self.visible = False
        self.font = pygame.font.SysFont(None, 24)

    def toggle(self) -> None:
        self.visible = not self.visible

    def draw(self, surface: pygame.Surface) -> None:
        if not self.visible:
            return
        th = get_theme()
        overlay = pygame.Surface(surface.get_size(), pygame.SRCALPHA)
        overlay.fill((*th.colors["bg"], 200))
        surface.blit(overlay, (0, 0))
        y = 40
        for action, key in self.input.bindings.items():
            key_name = pygame.key.name(key)
            btn = DEFAULT_GAMEPAD.get(action)
            txt = f"{_(action)}: {key_name}"
            if btn is not None:
                txt += f" / {btn}"
            img = self.font.render(txt, True, th.colors["text"])
            surface.blit(img, (40, y))
            y += 30
