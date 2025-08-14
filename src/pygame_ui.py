import pygame

from game_client import GameClient

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
    def draw_board(self) -> None:
        board = self.client.board
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
        for name, stats in self.client.players.items():
            health = stats.get("health", "?")
            items = len(stats.get("items", []))
            text = f"{name}: HP {health} Items {items}"
            surf = self.font.render(text, True, (255, 255, 255))
            self.screen.blit(surf, (x_offset, y))
            y += surf.get_height() + 5

    # ------------------------------------------------------------------
    def run(self) -> None:
        clock = pygame.time.Clock()
        running = True
        while running:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False

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
