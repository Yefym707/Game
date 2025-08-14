from entity import Entity


class Zombie(Entity):
    """Basic zombie that only tracks position and health."""

    def __init__(self, x: int = 0, y: int = 0, health: int = 3):
        super().__init__(x, y, health)
        self.attack_damage = 1

    def take_turn(self, players_list, game_board) -> None:
        """Move one step toward the nearest player or attack if adjacent.

        The board is represented as a 2D list where the first dimension
        corresponds to ``y`` (rows) and the second to ``x`` (columns).  The
        zombie will move horizontally or vertically by a single tile towards
        the closest player.  If the zombie starts its turn adjacent to a
        player it deals one point of damage instead of moving.

        Parameters
        ----------
        players_list:
            Iterable of player objects.  A player is expected to expose ``x``,
            ``y`` and ``take_damage`` attributes.
        game_board:
            2D board used to keep the zombie inside bounds.  The structure of
            the board itself is irrelevant – only its dimensions are used.
        """

        if not players_list:
            return

        # ------------------------------------------------------------------
        # determine nearest player using Manhattan distance
        def distance(p):
            return abs(p.x - self.x) + abs(p.y - self.y)

        target = min(players_list, key=distance)
        dx = target.x - self.x
        dy = target.y - self.y

        # If already adjacent (or on the same tile) attack instead of moving.
        if abs(dx) + abs(dy) <= 1:
            # Damage the player and stop. ``take_damage`` is the canonical API
            # but fall back to ``damage`` if necessary.
            if hasattr(target, "take_damage"):
                target.take_damage(self.attack_damage)
            elif hasattr(target, "damage"):
                target.damage(self.attack_damage)
            else:  # pragma: no cover - defensive
                target.health = max(0, target.health - self.attack_damage)
            return

        # ------------------------------------------------------------------
        # Move one step towards the target.
        if abs(dx) >= abs(dy):
            self.x += 1 if dx > 0 else -1
        else:
            self.y += 1 if dy > 0 else -1

        # Keep zombie on the board.
        height = len(game_board)
        width = len(game_board[0]) if height > 0 else 0
        self.x = max(0, min(self.x, width - 1))
        self.y = max(0, min(self.y, height - 1))
