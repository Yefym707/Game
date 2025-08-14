class GameBoard:
    """Simple grid-based game board.

    The board is represented by a two-dimensional list where each entry
    holds the entity occupying the tile or ``None`` if the tile is empty.
    Entities are expected to be represented by a single-character string
    such as ``"P"`` for the player or ``"Z"`` for a zombie. The class
    provides helpers to place and remove entities as well as query tile
    status and produce a text representation of the board.
    """

    def __init__(self, width: int = 10, height: int = 10):
        self.width = width
        self.height = height
        # initialise grid of None
        self.grid = [[None for _ in range(width)] for _ in range(height)]

    # ---------------------------------------------------------------
    # Tile helpers
    # ---------------------------------------------------------------
    def within_bounds(self, x: int, y: int) -> bool:
        """Return ``True`` if the coordinates are inside the board."""
        return 0 <= x < self.width and 0 <= y < self.height

    def is_tile_free(self, x: int, y: int) -> bool:
        """Return ``True`` if the tile is inside bounds and unoccupied."""
        return self.within_bounds(x, y) and self.grid[y][x] is None

    # ---------------------------------------------------------------
    # Manipulation
    # ---------------------------------------------------------------
    def place_entity(self, x: int, y: int, entity: str) -> None:
        """Place ``entity`` on the given tile.

        ``entity`` is typically a single character describing the occupant.
        Raises ``ValueError`` if the position is out of bounds or the tile
        is already occupied.
        """
        if not self.within_bounds(x, y):
            raise ValueError("Position out of bounds")
        if not self.is_tile_free(x, y):
            raise ValueError("Tile is already occupied")
        self.grid[y][x] = entity

    def remove_entity(self, x: int, y: int) -> None:
        """Remove any entity from the tile at ``(x, y)``.

        Raises ``ValueError`` if the coordinates are outside the board.
        """
        if not self.within_bounds(x, y):
            raise ValueError("Position out of bounds")
        self.grid[y][x] = None

    # ---------------------------------------------------------------
    # Display helpers
    # ---------------------------------------------------------------
    def display_board(self) -> str:
        """Return an ASCII representation of the board.

        Empty tiles are rendered as ``.`` while occupied tiles use the
        string representation of the stored entity. The board is returned
        as a multi-line string with each row separated by a newline.
        """
        lines = []
        for row in self.grid:
            line = ''.join(cell if cell is not None else '.' for cell in row)
            lines.append(line)
        return '\n'.join(lines)
