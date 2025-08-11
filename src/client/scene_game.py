"""In-game scene handling rendering and input."""
from __future__ import annotations

import math
import numpy as np
import pygame

from .app import Scene
from .gfx.tileset import TILE_SIZE, Tileset
from .ui.widgets import Log, StatusPanel
from gamecore import board as gboard
from gamecore import rules


def _tone(freq: int = 440, ms: int = 100) -> pygame.mixer.Sound:
    """Generate a simple tone sound."""

    sample_rate = 44100
    t = np.linspace(0, ms / 1000.0, int(sample_rate * ms / 1000.0), False)
    wave = (np.sin(freq * 2 * math.pi * t) * 32767).astype(np.int16)
    return pygame.sndarray.make_sound(wave)


class GameScene(Scene):
    """Render the board and process user input."""

    def __init__(self, app, new_game: bool = True) -> None:
        super().__init__(app)
        self.tileset = Tileset()
        self.state = gboard.create_game()
        rules.set_seed(0)
        self.camera_x = 0.0
        self.camera_y = 0.0
        self.scale = 1.0
        self.log = Log()
        self.status = StatusPanel()
        self._last_log = 0
        self.click_sound = _tone(880)
        self.move_sound = _tone(660)

    # event handling ---------------------------------------------------
    def handle_event(self, event: pygame.event.Event) -> None:
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                from .scene_menu import MenuScene

                self.next_scene = MenuScene(self.app)
            elif event.key == pygame.K_SPACE:
                gboard.end_turn(self.state)
            elif event.key in (pygame.K_UP, pygame.K_DOWN, pygame.K_LEFT, pygame.K_RIGHT):
                self._handle_move(event.key)
        elif event.type == pygame.MOUSEWHEEL:
            self.scale *= 1.25 if event.y > 0 else 0.8
            self.scale = max(0.75, min(2.0, self.scale))
        elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            self._handle_click(event.pos)

    def _handle_move(self, key: int) -> None:
        mapping = {
            pygame.K_UP: "w",
            pygame.K_DOWN: "s",
            pygame.K_LEFT: "a",
            pygame.K_RIGHT: "d",
        }
        if gboard.player_move(self.state, mapping[key]):
            self.move_sound.play()

    def _handle_click(self, pos) -> None:
        mx, my = pos
        tile_size = int(TILE_SIZE * self.scale)
        x = int((mx + self.camera_x) // tile_size)
        y = int((my + self.camera_y) // tile_size)
        if self.state.board.in_bounds(x, y):
            msg = f"clicked {(x, y)}"
            self.state.add_log(msg)
            self.click_sound.play()

    # update / draw ----------------------------------------------------
    def update(self, dt: float) -> None:
        pressed = pygame.key.get_pressed()
        speed = 400 * dt
        if pressed[pygame.K_w]:
            self.camera_y -= speed
        if pressed[pygame.K_s]:
            self.camera_y += speed
        if pressed[pygame.K_a]:
            self.camera_x -= speed
        if pressed[pygame.K_d]:
            self.camera_x += speed
        if len(self.state.log) > self._last_log:
            for msg in self.state.log[self._last_log :]:
                self.log.add(msg)
            self._last_log = len(self.state.log)

    def draw(self, surface: pygame.Surface) -> None:
        surface.fill((0, 0, 0))
        tile_size = int(TILE_SIZE * self.scale)
        board = self.state.board
        for y, row in enumerate(board.tiles):
            for x, ch in enumerate(row):
                tile = self.tileset.get(ch)
                if tile:
                    if tile_size != TILE_SIZE:
                        img = pygame.transform.scale(tile, (tile_size, tile_size))
                    else:
                        img = tile
                    sx = x * tile_size - self.camera_x
                    sy = y * tile_size - self.camera_y
                    surface.blit(img, (sx, sy))
        # entities
        self._draw_entity(surface, self.state.player, tile_size)
        for z in self.state.zombies:
            self._draw_entity(surface, z, tile_size)
        # UI
        w, h = surface.get_size()
        log_rect = pygame.Rect(w - 200, 0, 200, h)
        self.log.draw(surface, log_rect)
        self.status.draw(surface, self.state)

    def _draw_entity(self, surface: pygame.Surface, ent, tile_size: int) -> None:
        tile = self.tileset.get(ent.symbol)
        if tile:
            if tile_size != TILE_SIZE:
                img = pygame.transform.scale(tile, (tile_size, tile_size))
            else:
                img = tile
            sx = ent.x * tile_size - self.camera_x
            sy = ent.y * tile_size - self.camera_y
            surface.blit(img, (sx, sy))
