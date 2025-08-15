"""Simple entry point with a basic pygame main menu."""

import os
import sys

import pygame

# ensure local ``src`` modules are importable when running this file directly
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "src"))

from cli import _load_locale  # type: ignore
from pygame_ui import PygameUI  # type: ignore
from game_client import GameClient  # type: ignore
from campaign import Campaign  # type: ignore
from main import load_scenarios, _data_path  # type: ignore


def _run_game() -> None:
    client = GameClient()
    ui = PygameUI(client)
    ui.run()


def main() -> None:
    pygame.init()
    screen = pygame.display.set_mode((640, 480))
    font = pygame.font.SysFont("consolas", 30)
    locale = _load_locale()
    options = [
        locale.get("menu_new_game", "New Game"),
        locale.get("menu_load", "Load"),
        locale.get("menu_quit", "Quit"),
    ]
    selected = 0
    running = True
    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.KEYDOWN:
                if event.key in (pygame.K_DOWN, pygame.K_s):
                    selected = (selected + 1) % len(options)
                elif event.key in (pygame.K_UP, pygame.K_w):
                    selected = (selected - 1) % len(options)
                elif event.key in (pygame.K_RETURN, pygame.K_SPACE):
                    if selected == 0:  # New game
                        pygame.quit()
                        _run_game()
                        pygame.init()
                        screen = pygame.display.set_mode((640, 480))
                    elif selected == 1:  # Load
                        path = _data_path("savegame.json")
                        if os.path.exists(path):
                            try:
                                Campaign.load(path, load_scenarios())
                                pygame.quit()
                                _run_game()
                                pygame.init()
                                screen = pygame.display.set_mode((640, 480))
                            except Exception:
                                pass
                        else:
                            # flash a small message for missing save
                            surf = font.render(
                                locale.get("no_valid_save", "No save"), True, (255, 0, 0)
                            )
                            screen.blit(surf, (10, 10))
                            pygame.display.flip()
                            pygame.time.delay(1000)
                    else:
                        running = False

        screen.fill((0, 0, 0))
        for i, text in enumerate(options):
            color = (255, 255, 0) if i == selected else (200, 200, 200)
            surf = font.render(text, True, color)
            rect = surf.get_rect(center=(320, 200 + i * 40))
            screen.blit(surf, rect)
        pygame.display.flip()

    pygame.quit()


if __name__ == "__main__":  # pragma: no cover - manual execution only
    main()

