"""Photo mode scene providing a free camera and screenshot support."""
from __future__ import annotations

import pygame

from .app import Scene
from .gfx.camera import SmoothCamera
from .gfx import postfx
from gamecore import config as gconfig, rules


class PhotoScene(Scene):
    """Frozen snapshot of :class:`~client.scene_game.GameScene` with controls."""

    def __init__(self, app, base_scene) -> None:
        super().__init__(app)
        self.base = base_scene
        self.camera: SmoothCamera = base_scene.camera
        self.dragging = False
        self.hide_ui = False

    # ------------------------------------------------------------------
    # event handling
    # ------------------------------------------------------------------
    def handle_event(self, event: pygame.event.Event) -> None:  # pragma: no cover - GUI only
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_F10:
                self.next_scene = self.base
                return
            if event.key == pygame.K_h:
                self.hide_ui = not self.hide_ui
                return
            if event.key == pygame.K_F12:
                self._capture()
                return
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            self.dragging = True
        elif event.type == pygame.MOUSEBUTTONUP and event.button == 1:
            self.dragging = False
        elif event.type == pygame.MOUSEMOTION and self.dragging:
            dx, dy = event.rel
            self.camera.target_x -= dx / self.camera.zoom
            self.camera.target_y -= dy / self.camera.zoom
        elif event.type == pygame.MOUSEWHEEL:
            self.camera.zoom_at(event.y, event.pos)

    # ------------------------------------------------------------------
    def _capture(self) -> None:  # pragma: no cover - GUI only
        """Save current frame as a screenshot."""

        path = gconfig.screenshot_path(getattr(rules.RNG, "_seed", 0))
        surface = self.app.screen.copy()
        watermark = None
        if rules.DEMO_MODE and rules.DEMO_WATERMARK:
            font = pygame.font.SysFont(None, 48)
            watermark = font.render(rules.DEMO_WATERMARK, True, (255, 255, 255))
            watermark.set_alpha(128)
        postfx.export_frame(surface, path, self.app.cfg, watermark)

    # ------------------------------------------------------------------
    def update(self, dt: float) -> None:  # pragma: no cover - GUI only
        keys = pygame.key.get_pressed()
        speed = 300.0 * dt / self.camera.zoom
        if keys[pygame.K_w]:
            self.camera.target_y -= speed
        if keys[pygame.K_s]:
            self.camera.target_y += speed
        if keys[pygame.K_a]:
            self.camera.target_x -= speed
        if keys[pygame.K_d]:
            self.camera.target_x += speed
        self.camera.update(dt)

    # ------------------------------------------------------------------
    def draw(self, surface: pygame.Surface) -> None:  # pragma: no cover - GUI only
        self.base.draw(surface, ui=not self.hide_ui)
