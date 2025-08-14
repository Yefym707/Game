"""Minimal graphical front end built on :mod:`pygame`.

The original version of this module only displayed the game board.  The updated
implementation wires the renderer into a very small local game loop so the
player can control a character directly.  Keyboard input is processed to move
the hero, attack nearby zombies, search the current tile or end the turn.  Once
the player has acted the zombies perform their moves before a new round starts.
The display is refreshed every frame and a small flash effect highlights attack
targets.  The module purposefully keeps the mechanics lightweight – it is meant
as a playable demonstration rather than a full game client.
"""

import pygame

from game_client import GameClient
from dice import roll
from player import Player
from zombie import Zombie

CELL_SIZE = 32
MARGIN = 200  # width for stats area

COLORS = {
    "empty": (40, 40, 40),
    "player": (0, 100, 255),
    "zombie": (200, 30, 30),
    "item": (220, 220, 0),
}


class PygameUI:
    """Simple graphical renderer for :class:`GameClient` state.

    The renderer uses a blocky pixel-art style by drawing coloured squares
    for the entities on the board.  Player statistics are displayed to the
    right of the board and refreshed each frame.
    """

    def __init__(self, client: GameClient, cell_size: int = CELL_SIZE) -> None:
        self.client = client
        self.cell_size = cell_size

        pygame.init()
        width = client.board.width * cell_size + MARGIN
        height = client.board.height * cell_size
        self.screen = pygame.display.set_mode((width, height))
        pygame.display.set_caption("Survival Game")
        self.font = pygame.font.SysFont("consolas", 18)

        # ------------------------------------------------------------------
        # Local game state used for the demo mode.  A single player is placed on
        # the board together with a zombie.  ``GameClient`` is still used for the
        # board representation which keeps this module loosely coupled from the
        # rest of the project.
        # ------------------------------------------------------------------
        self.player = Player(x=1, y=1, name="Hero")
        try:
            self.client.board.place_entity(self.player.x, self.player.y, "P")
        except ValueError:
            pass  # board might already contain data when connected to a server

        # Spawn a single zombie a few tiles away for demonstration purposes.
        zx = max(0, self.client.board.width - 2)
        zy = max(0, self.client.board.height - 2)
        self.zombies: list[Zombie] = [Zombie(zx, zy)]
        try:
            self.client.board.place_entity(zx, zy, "Z")
        except ValueError:
            pass

        # The player starts the first turn with a random number of actions.
        self.player.start_turn(roll("1d6")[0])

        # Flash state used to highlight tiles that were recently attacked.
        self._flash_pos: tuple[int, int] | None = None
        self._flash_until: int = 0

    # ------------------------------------------------------------------
    def draw_board(self) -> None:
        board = self.client.board
        now = pygame.time.get_ticks()
        for y, row in enumerate(board.grid):
            for x, cell in enumerate(row):
                rect = pygame.Rect(
                    x * self.cell_size,
                    y * self.cell_size,
                    self.cell_size,
                    self.cell_size,
                )
                color = COLORS["empty"]
                if cell == "P":
                    color = COLORS["player"]
                elif cell == "Z":
                    color = COLORS["zombie"]
                elif cell == "I":
                    color = COLORS["item"]
                pygame.draw.rect(self.screen, color, rect)
                # highlight recently attacked tiles
                if self._flash_pos == (x, y) and now < self._flash_until:
                    pygame.draw.rect(self.screen, (255, 255, 255), rect, 2)
                pygame.draw.rect(self.screen, (25, 25, 25), rect, 1)

    # ------------------------------------------------------------------
    def draw_stats(self) -> None:
        x_offset = self.client.board.width * self.cell_size + 10
        y = 10
        pygame.draw.rect(
            self.screen,
            (20, 20, 20),
            pygame.Rect(
                self.client.board.width * self.cell_size,
                0,
                MARGIN,
                self.client.board.height * self.cell_size,
            ),
        )
        # ``GameClient`` maintains a mapping of players which is used when the
        # UI is connected to a real server.  For the standalone demo we render
        # statistics directly from the local player object.
        if self.client.players:
            iterable = [
                (name, stats.get("health", "?"), len(stats.get("items", [])))
                for name, stats in self.client.players.items()
            ]
        else:
            item_count = sum(self.player.inventory.items.values())
            iterable = [(self.player.name, self.player.health, item_count)]

        for name, health, items in iterable:
            text = f"{name}: HP {health} Items {items}"
            surf = self.font.render(text, True, (255, 255, 255))
            self.screen.blit(surf, (x_offset, y))
            y += surf.get_height() + 5

    # ------------------------------------------------------------------
    def run(self) -> None:
        """Main interactive loop.

        The loop listens for keyboard input and translates it into actions on
        the player character.  Once the player has used up their actions or
        explicitly ends their turn the zombies take their moves.  The board is
        redrawn every iteration to reflect the current state.
        """

        clock = pygame.time.Clock()
        running = True
        while running:
            # ------------------------------------------------------------------
            # handle input
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
                elif event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_ESCAPE:
                        running = False
                    # movement -------------------------------------------------
                    elif event.key in (
                        pygame.K_UP,
                        pygame.K_DOWN,
                        pygame.K_LEFT,
                        pygame.K_RIGHT,
                    ):
                        if event.key == pygame.K_UP:
                            dx, dy = 0, -1
                        elif event.key == pygame.K_DOWN:
                            dx, dy = 0, 1
                        elif event.key == pygame.K_LEFT:
                            dx, dy = -1, 0
                        else:  # pygame.K_RIGHT
                            dx, dy = 1, 0
                        self.player.move(dx, dy, self.client.board)

                    # attack ---------------------------------------------------
                    elif event.key in (pygame.K_a, pygame.K_SPACE):
                        for z in list(self.zombies):
                            if abs(z.x - self.player.x) + abs(z.y - self.player.y) == 1:
                                if self.player.attack(z):
                                    self._flash_pos = (z.x, z.y)
                                    self._flash_until = pygame.time.get_ticks() + 200
                                    if z.health <= 0:
                                        self.client.board.remove_entity(z.x, z.y)
                                        self.zombies.remove(z)
                                break

                    # search ---------------------------------------------------
                    elif event.key == pygame.K_s:
                        self.player.search(self.client.board)

                    # end turn -------------------------------------------------
                    elif event.key in (pygame.K_e, pygame.K_RETURN):
                        self.player.end_turn()

            # ------------------------------------------------------------------
            # enemy phase
            if self.player.turn_over:
                for z in list(self.zombies):
                    old = (z.x, z.y)
                    adjacent = (
                        abs(z.x - self.player.x) + abs(z.y - self.player.y) == 1
                    )
                    z.take_turn([self.player], self.client.board.grid)
                    self.client.board.remove_entity(*old)
                    if z.health > 0:
                        self.client.board.place_entity(z.x, z.y, "Z")
                    if adjacent and (z.x, z.y) == old:
                        self._flash_pos = (self.player.x, self.player.y)
                        self._flash_until = pygame.time.get_ticks() + 200

                if self.player.health <= 0:
                    running = False
                else:
                    # start a new player turn with fresh actions
                    self.player.start_turn(roll("1d6")[0])

            # ------------------------------------------------------------------
            # draw frame
            self.draw_board()
            self.draw_stats()
            pygame.display.flip()
            clock.tick(60)

        pygame.quit()


def main() -> None:  # pragma: no cover - manual graphical demo only
    """Launch the renderer and connect to a server on localhost."""

    client = GameClient()
    # In a real application we would connect to a server here.  For this
    # simple demo, the board will just stay empty until :class:`GameClient`
    # receives updates from elsewhere.
    ui = PygameUI(client)
    ui.run()


if __name__ == "__main__":  # pragma: no cover - manual graphical demo only
    main()
