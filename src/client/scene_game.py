"""In-game scene handling rendering and input."""
from __future__ import annotations

import asyncio
import pygame

from .app import Scene
from .gfx.tileset import TILE_SIZE, Tileset
from .ui.widgets import Log, StatusPanel
from .input import InputManager
from .sfx import SFX, set_volume
from .net_client import NetClient
from gamecore import board as gboard
from gamecore import rules, saveio, config as gconfig, achievements

try:  # pragma: no cover - optional dependency
    import pygame.messagebox as messagebox
except Exception:  # pragma: no cover - fallback if missing
    messagebox = None


class GameScene(Scene):
    """Render the board and process user input."""

    def __init__(self, app, new_game: bool = True, net_client: NetClient | None = None) -> None:
        super().__init__(app)
        self.cfg = app.cfg
        set_volume(self.cfg.get("volume", 1.0))
        self.input: InputManager = app.input
        self.tileset = Tileset()
        self.quick_path = gconfig.quicksave_path()
        self.autosave_path = gconfig.autosave_path()
        self.net_client = net_client
        if new_game:
            pconf = self.cfg.get("players")
            count = len(pconf) if isinstance(pconf, list) and pconf else 1
            mode = rules.GameMode.LOCAL_COOP if count > 1 else rules.GameMode.SOLO
            self.state = gboard.create_game(players=count, mode=mode)
            if isinstance(pconf, list):
                for pdata, player in zip(pconf, self.state.players):
                    player.name = pdata.get("name", player.name)
                    player.color = pdata.get("color", player.color)
            achievements.on_game_start(len(self.state.players))
        else:
            try:
                self.state = saveio.load_game(self.autosave_path)
            except Exception as exc:
                self.state = gboard.create_game()
                self._show_error(str(exc))
            achievements.on_game_start(len(self.state.players))
        rules.set_seed(0)
        self.camera_x = 0.0
        self.camera_y = 0.0
        self.scale = 1.0
        self.log = Log()
        self.status = StatusPanel()
        self._last_log = 0
        self.sfx = SFX()
        self.input.set_profile(self.state.active)

    def _show_error(self, msg: str) -> None:
        """Display an error message without crashing."""

        if messagebox:
            try:
                messagebox.show("Error", msg)
                return
            except Exception:  # pragma: no cover - fallback
                pass
        # Fallback to console/log output
        print("Error:", msg)
        if hasattr(self, "log"):
            self.log.add(msg)

    # event handling ---------------------------------------------------
    def handle_event(self, event: pygame.event.Event) -> None:
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                from .scene_menu import MenuScene

                self.next_scene = MenuScene(self.app)
                return
            action = self.input.action_from_key(event.key)
            if action == "pause":
                from .scene_menu import MenuScene

                self.next_scene = MenuScene(self.app)
            elif action == "end_turn":
                if self.state.mode == rules.GameMode.ONLINE and self.net_client:
                    asyncio.create_task(self.net_client.send({"t": "ACTION", "p": {"end_turn": True}}))
                else:
                    gboard.end_turn(self.state)
                    self.input.set_profile(self.state.active)
                    try:
                        saveio.save_game(self.state, self.autosave_path)
                    except Exception as exc:
                        self._show_error(str(exc))
            elif action == "quick_save":
                if self.state.mode != rules.GameMode.ONLINE:
                    try:
                        saveio.save_game(self.state, self.quick_path)
                    except Exception as exc:
                        self._show_error(str(exc))
            elif action == "quick_load":
                if self.state.mode != rules.GameMode.ONLINE:
                    try:
                        self.state = saveio.load_game(self.quick_path)
                        self.log.lines.clear()
                        self._last_log = 0
                        self.input.set_profile(self.state.active)
                    except Exception as exc:
                        self._show_error(str(exc))
            elif action in ("move_up", "move_down", "move_left", "move_right"):
                self._handle_move(action)
            elif action == "rest":
                self.state.add_log("rest")
                achievements.on_campaign_win()
            elif action == "scavenge":
                self.state.add_log("scavenge")
        elif event.type == pygame.MOUSEWHEEL:
            self.scale *= 1.25 if event.y > 0 else 0.8
            self.scale = max(0.75, min(2.0, self.scale))
        elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            self._handle_click(event.pos)

    def _handle_move(self, action: str) -> None:
        mapping = {
            "move_up": "w",
            "move_down": "s",
            "move_left": "a",
            "move_right": "d",
        }
        if self.state.mode == rules.GameMode.ONLINE and self.net_client:
            asyncio.create_task(
                self.net_client.send({"t": "ACTION", "p": {"move": mapping[action]}})
            )
        else:
            if gboard.player_move(self.state, mapping[action]):
                self.sfx.play("step")

    def _handle_click(self, pos) -> None:
        mx, my = pos
        tile_size = int(TILE_SIZE * self.scale)
        x = int((mx + self.camera_x) // tile_size)
        y = int((my + self.camera_y) // tile_size)
        if self.state.board.in_bounds(x, y):
            msg = f"clicked {(x, y)}"
            self.state.add_log(msg)
            self.sfx.play("pickup")
            achievements.on_zombie_kill()

    # update / draw ----------------------------------------------------
    def update(self, dt: float) -> None:
        if rules.DEMO_MODE and self.state.turn >= rules.DEMO_MAX_DAYS:
            from .scene_demo_end import DemoEndScene

            self.next_scene = DemoEndScene(self.app)
            return
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
        for p in self.state.players:
            self._draw_entity(surface, p, tile_size)
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
